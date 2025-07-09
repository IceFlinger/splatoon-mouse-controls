import pygame

pygame.init()
screen = pygame.display.set_mode((600,600))
clock = pygame.time.Clock()
running = True

mouse_sens = 50

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill("purple")

    pygame.mouse.set_pos([300,300])
    dx, dy = pygame.mouse.get_rel()
    val_pitch = (dy*mouse_sens)%0xFFFF
    val_yaw = (dx*mouse_sens)%0xFFFF
    print(str(val_pitch) + " " + str(val_yaw))

    pygame.display.flip()

    clock.tick(120) 

pygame.quit()
