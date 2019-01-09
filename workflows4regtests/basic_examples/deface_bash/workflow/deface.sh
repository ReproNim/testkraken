#!/usr/bin/env bash
#
# Deface MRI scan.

set -e

# Get command-line options.
while getopts 'i:' flag; do
  case "${flag}" in
    i) INFILE="${OPTARG}" ;;
    *) echo 'Usage: deface.sh -i INPUT'
       exit 1 ;;
  esac
done

if [ ! -f "$INFILE" ]; then
  echo "error: file does not exist: $1"
  exit 1;
fi

# Brain extraction with FSL.
bet $INFILE brain.nii.gz -m

# Defacing with Quickshear.
quickshear $INFILE brain_mask.nii.gz T1_defaced.nii.gz
