"""Edit worker: pulls jobs from the queue and edits them. Run as many copies as you need:

    python -m cuttit.worker
"""

import logging
import shutil
import time
from pathlib import Path

from . import jobs, storage
from .config import settings
from .models import ClipTranscript, EditPlan
from .pipeline import edit_video

log = logging.getLogger("cuttit.worker")

# Called after a video is ready, e.g. to send it on WhatsApp. The bot sets this.
on_video_ready = None


def process(conn, job: dict) -> None:
    video = jobs.get_video(conn, job["video_id"])
    client_id, video_id, kind = str(video["client_id"]), str(video["id"]), job["kind"]
    work = Path(settings.work_dir) / video_id / f"{kind}-{job['id']}"
    try:
        clips = [storage.download(k, work / "raw" / f"{i}{Path(k).suffix or '.mp4'}")
                 for i, k in enumerate(video["clip_keys"])]
        if not clips:
            raise RuntimeError("video has no clips")
        transcripts = ([ClipTranscript.model_validate(t) for t in video["transcript"]]
                       if video["transcript"] else None)
        previous = EditPlan.model_validate(video["plan"]) if (kind == "final" and video["plan"]) else None

        result = edit_video(clips, video["style"], work / f"{kind}.mp4", work, kind=kind,
                            transcripts=transcripts, previous=previous,
                            feedback=video["feedback"] if kind == "final" else None)

        key = storage.upload(result.video, storage.output_key(client_id, video_id, kind))
        jobs.save_result(conn, video_id, kind, key, result.plan.model_dump(),
                         [t.model_dump() for t in result.transcripts])
        log.info("video %s %s ready (%.0fs): %s", video_id, kind, result.seconds, result.plan.notes)
        if on_video_ready:
            on_video_ready(video_id, kind, storage.share_link(key))
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run_forever(poll_seconds: float = 3.0) -> None:
    log.info("worker %s started", jobs.WORKER_ID)
    last_sweep = 0.0
    while True:
        with jobs.connect() as conn:
            if time.time() - last_sweep > 300:
                jobs.requeue_stale(conn)
                conn.commit()
                last_sweep = time.time()
            job = jobs.claim(conn)
            conn.commit()
            if not job:
                time.sleep(poll_seconds)
                continue
            try:
                process(conn, job)
                jobs.finish(conn, job["id"])
            except Exception as exc:  # keep the worker alive whatever one job does
                conn.rollback()
                log.exception("job %s failed", job["id"])
                retry = jobs.fail(conn, job, f"{type(exc).__name__}: {exc}")
                log.info("job %s %s", job["id"], "will retry" if retry else "gave up")
            conn.commit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_forever()
