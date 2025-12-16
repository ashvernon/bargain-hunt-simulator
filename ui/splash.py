import time
from pathlib import Path

import pygame
from moviepy.editor import VideoFileClip

from config import GameConfig


def play_splash(screen: pygame.Surface, clock: pygame.time.Clock, cfg: GameConfig) -> bool:
    """Play the intro splash video and return False if the window is closed."""
    video_path = Path(cfg.splash_video_path)
    if not cfg.show_splash:
        return True

    if not video_path.exists():
        print(f"Splash video not found at {video_path}; skipping intro.")
        return True

    clip = VideoFileClip(str(video_path))
    duration = min(cfg.splash_duration, clip.duration)
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
                clip.close()
                return True

        frame_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        screen.fill((0, 0, 0))
        screen.blit(frame_surface, offset)
        pygame.display.flip()
        clock.tick(clip.fps)

    clip.close()
    return True
