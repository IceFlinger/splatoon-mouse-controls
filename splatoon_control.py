import pygame

pygame.init()
screen = pygame.display.set_mode((600,600))
clock = pygame.time.Clock()
running = True
#focused = False

mouse_sens = 50

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill("purple")
    if pygame.key.get_focused():
        pygame.mouse.set_pos([300,300])
    dx, dy = pygame.mouse.get_rel()
    val_pitch = (dy*mouse_sens)%0xFFFF
    val_yaw = (dx*mouse_sens)%0xFFFF
    if [val_pitch, val_yaw] != [0,0]:
        print(str(val_pitch) + " " + str(val_yaw))

    pygame.display.flip()

    clock.tick(120) 

pygame.quit()
