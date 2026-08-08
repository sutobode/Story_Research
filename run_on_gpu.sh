#!/usr/bin/env bash
# Usage:
#   ./run_on_gpu.sh <script.py> [args...]   -> chạy nhanh trên login node (không qua Slurm) — dùng để test nhanh
#   ./run_on_gpu.sh --train <script.py>     -> submit job huấn luyện/tính toán lớn qua Slurm (sbatch) trên A100
#   ./run_on_gpu.sh --status                -> xem squeue (job đang chờ/chạy)
#   ./run_on_gpu.sh --log [jobid]           -> xem slurm-<jobid>.out (mặc định: file mới nhất)
#   ./run_on_gpu.sh --cancel <jobid>        -> scancel 1 job
#
# Lưu ý: KHÔNG sửa file run_via_slurm. File `script` chỉ được sửa đúng dòng chứa lệnh python.
set -e

MUTAGEN="mutagen.exe"
REMOTE_HOST="a100-B"
REMOTE_DIR="~/thuongnm_hust/Story_Research"
CONDA_ENV="story_research"
CONDA_SH="/data2/shared/apps/conda/etc/profile.d/conda.sh"

MODE="quick"
case "$1" in
  --train)  MODE="train"; shift ;;
  --status) MODE="status"; shift ;;
  --log)    MODE="log"; shift ;;
  --cancel) MODE="cancel"; shift ;;
esac

"$MUTAGEN" sync flush story-research >/dev/null

case "$MODE" in
  quick)
    SCRIPT="$1"
    shift || true
    ssh "$REMOTE_HOST" "source $CONDA_SH && conda activate $CONDA_ENV && cd $REMOTE_DIR && python $SCRIPT $*"
    ;;

  train)
    SCRIPT="$1"
    REMOTE_CMD="cd $REMOTE_DIR && sed -i '12s#.*#python $SCRIPT#' script && conda activate $CONDA_ENV && . run_via_slurm && sleep 2 && squeue -u \$USER"
    ssh "$REMOTE_HOST" "bash -lic \"$REMOTE_CMD\""
    ;;

  status)
    ssh "$REMOTE_HOST" "bash -lic \"squeue -u \$USER\""
    ;;

  log)
    JOBID="$1"
    if [ -z "$JOBID" ]; then
      ssh "$REMOTE_HOST" "cd $REMOTE_DIR && ls -t slurm-*.out 2>/dev/null | head -1 | xargs cat"
    else
      ssh "$REMOTE_HOST" "cat $REMOTE_DIR/slurm-$JOBID.out"
    fi
    ;;

  cancel)
    JOBID="$1"
    ssh "$REMOTE_HOST" "bash -lic \"scancel $JOBID\""
    ;;
esac
