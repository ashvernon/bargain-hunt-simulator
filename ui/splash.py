import time
from pathlib import Path

import pygame

try:
    from moviepy.editor import VideoFileClip
except ImportError:
    VideoFileClip = None

from config import GameConfig


def play_splash(screen: pygame.Surface, clock: pygame.time.Clock, cfg: GameConfig) -> bool:
    """Play the intro splash video and return False if the window is closed."""
    video_path = Path(cfg.splash_video_path)
    if not cfg.show_splash_video:
        return True

    if VideoFileClip is None:
        print("moviepy is not installed; skipping intro video.")
        return True

    if not video_path.exists():
        print(f"Splash video not found at {video_path}; skipping intro.")
        return True

    try:
        clip = VideoFileClip(str(video_path))
    except Exception as exc:  # noqa: BLE001
        print(f"Could not load splash video at {video_path}; skipping intro. ({exc})")
        return True

    duration = min(cfg.splash_video_max_seconds, clip.duration)
    scale = min(cfg.window_w / clip.w, cfg.window_h / clip.h)
    new_size = (int(clip.w * scale), int(clip.h * scale))
    offset = ((cfg.window_w - new_size[0]) // 2, (cfg.window_h - new_size[1]) // 2)
    resized_clip = clip.resize(newsize=new_size)

    start = time.perf_counter()
    for frame in resized_clip.iter_frames(fps=clip.fps, dtype="uint8"):
        elapsed = time.perf_counter() - start
        if elapsed >= duration:
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                clip.close()
                return False
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                if event.type == pygame.KEYDOWN and event.key not in (pygame.K_ESCAPE, pygame.K_SPACE):
                    # Only specific keys skip the video to avoid accidental dismissals.
                    continue
                clip.close()
                return True

        frame_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        screen.fill((0, 0, 0))
        screen.blit(frame_surface, offset)
        pygame.display.flip()
        clock.tick(clip.fps)

    clip.close()
    return True
