#!/usr/bin/env bash
# Build the manuscript and the supplement with host lualatex.
#
# Every intermediate file goes to draft/build/ (git-ignored) and only the PDFs
# are moved back into draft/. Running lualatex by hand inside draft/ leaves
# .aux/.bbl files there that a later build picks up silently, which produces a
# PDF with missing or outdated references.
#
# Usage:
#   bash draft/compile.sh            # draft/main.pdf and draft/supplementary.pdf
#   bash draft/compile.sh --review   # the manuscript with line numbers and double
#                                    # spacing, as draft/main_review.pdf
#
# After result/tables/*.csv change, run `make numbers` (in the container) first,
# or `make paper` for both. The lualatex transcripts go to draft/build/<job>.log
# and only errors are printed. The script exits non-zero when a citation or a
# reference is still undefined, after writing the PDFs.
set -euo pipefail

draft_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
build_dir="${draft_dir}/build"

# --review: many journals ask for line numbers and double spacing at
# submission. The output gets its own name so it is never mistaken for the
# final version. The text is identical: main.tex switches only its layout on
# \reviewformat.
main_source="main.tex"
main_output="main.pdf"
if [ "${1:-}" = "--review" ]; then
  main_source='\def\reviewformat{}\input{main.tex}'
  main_output="main_review.pdf"
elif [ -n "${1:-}" ]; then
  echo "Unknown option: $1 (expected --review or nothing)" >&2
  exit 2
fi

mkdir -p "${build_dir}"
cd "${draft_dir}"

# \include{sections/intro} writes build/sections/intro.aux, and TeX does not
# create that directory itself: mirror the subdirectories of draft/ in build/.
find . -mindepth 1 -type d ! -path './build' ! -path './build/*' -print0 |
  while IFS= read -r -d '' dir; do
    mkdir -p "${build_dir}/${dir#./}"
  done

# Let TeX and BibTeX find sources, bibliographies and a journal's .bst in
# draft/ while writing everything to build/.
export TEXINPUTS="${build_dir}:${draft_dir}:${TEXINPUTS:-}"
export BIBINPUTS="${draft_dir}:${BIBINPUTS:-}"
export BSTINPUTS="${draft_dir}:${BSTINPUTS:-}"

# cites <aux>: true if the .aux file, or one it pulls in with \@input (as
# \include does), records a citation.
cites() {
  local aux="$1" child
  grep -q '\\citation' "${aux}" && return 0
  while IFS= read -r child; do
    if [ -f "${build_dir}/${child}" ] && cites "${build_dir}/${child}"; then
      return 0
    fi
  done < <(sed -n 's/^\\@input{\(.*\)}$/\1/p' "${aux}")
  return 1
}

# run_lualatex <jobname> <source>: one pass, with its transcript in the log
# only. On an error, print the file:line messages from the log and stop.
run_lualatex() {
  local job="$1" source="$2"
  if ! lualatex -interaction=nonstopmode -halt-on-error -file-line-error \
      -output-directory="${build_dir}" -jobname="${job}" "${source}" > /dev/null; then
    echo "lualatex failed on ${job} (${build_dir}/${job}.log):" >&2
    grep -E -A 3 '^[^ ]+:[0-9]+: |^! ' "${build_dir}/${job}.log" >&2 || tail -n 30 "${build_dir}/${job}.log" >&2
    exit 1
  fi
}

# build <jobname> <source>: lualatex, BibTeX if the document has a
# bibliography and cites something, then lualatex twice to settle citations
# and cross-references. BibTeX stops with an error on a bibliography that
# nothing cites yet, as in a fresh project.
build() {
  local job="$1" source="$2"
  echo "Building ${job}"
  run_lualatex "${job}" "${source}"
  if grep -q '\\bibdata' "${build_dir}/${job}.aux" && cites "${build_dir}/${job}.aux"; then
    # BibTeX exits 1 for warnings (an empty field, for example) and 2 or more
    # for errors. Warnings are printed; only errors stop the build.
    local status=0
    (cd "${build_dir}" && bibtex "${job}") || status=$?
    if [ "${status}" -gt 1 ]; then
      exit "${status}"
    fi
  else
    # Without BibTeX, a .bbl left by an earlier build would still be read and
    # print references the document no longer cites.
    rm -f "${build_dir}/${job}.bbl"
  fi
  run_lualatex "${job}" "${source}"
  run_lualatex "${job}" "${source}"
}

# unresolved <jobname>: TeX exits 0 when a citation or a reference is
# undefined, so read what the last pass reported.
unresolved() {
  grep -E '(Citation|Reference) .*undefined|There were undefined' "${build_dir}/$1.log"
}

# Move each PDF as soon as it is built, so that a failure in the supplement
# still leaves the manuscript.
build main "${main_source}"
mv "${build_dir}/main.pdf" "${draft_dir}/${main_output}"
build supplementary supplementary.tex
mv "${build_dir}/supplementary.pdf" "${draft_dir}/supplementary.pdf"
echo "Built ${draft_dir}/${main_output} and ${draft_dir}/supplementary.pdf"

status=0
for job in main supplementary; do
  if unresolved "${job}" >&2; then
    echo "Undefined citations or references in ${job}: see ${build_dir}/${job}.log" >&2
    status=1
  fi
done
exit "${status}"
