import pygame

from hotlapper.domain.controls import Command, Controls


def _command_for(key: int) -> Command | None:
    match key:
        case pygame.K_ESCAPE:
            return Command.BACK
        case pygame.K_F11:
            return Command.FULLSCREEN
        case _:
            return None


class PygameKeyboard:
    def poll(self) -> Controls:
        commands: list[Command] = []
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    commands.append(Command.QUIT)
                case pygame.KEYDOWN:
                    command = _command_for(event.key)
                    if command is not None:
                        commands.append(command)
        held = pygame.key.get_pressed()
        return Controls(
            steer_left_fast=held[pygame.K_a],
            steer_left_slow=held[pygame.K_s],
            steer_right_slow=held[pygame.K_d],
            steer_right_fast=held[pygame.K_f],
            accelerate=held[pygame.K_i],
            brake=held[pygame.K_k],
            commands=tuple(commands),
        )
