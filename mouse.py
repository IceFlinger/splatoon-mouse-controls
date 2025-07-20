import pygame
from nxbt import nxbt

pygame.init()
screen = pygame.display.set_mode((1200,1200))
clock = pygame.time.Clock()
running = True

mouse_sens_x = 50
mouse_sens_y = 150

switch_addr = None

nx = nxbt.Nxbt()
index = nx.create_controller(nxbt.PRO_CONTROLLER, reconnect_address=switch_addr)


print("Connecting controller to switch... (Go to Change Grip/Order and trust the switch from bluetoothctl on PC)")
nx.wait_for_connection(index)
print("Connected!")

packet = nx.create_input_packet()
packet["IMU_DATA"] = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

framecount = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if pygame.key.get_pressed()[pygame.K_ESCAPE]:
        running = False

    stick_x = 0
    stick_y = 0

    if pygame.key.get_pressed()[pygame.K_w]:
        stick_y += 100
    if pygame.key.get_pressed()[pygame.K_a]:
        stick_x -= 100
    if pygame.key.get_pressed()[pygame.K_s]:
        stick_y -= 100
    if pygame.key.get_pressed()[pygame.K_d]:
        stick_x += 100

    packet['L_STICK']['X_VALUE'] = stick_x
    packet['L_STICK']['Y_VALUE'] = stick_y

    if pygame.mouse.get_pressed()[1]:
        packet['R_STICK']['PRESSED'] = True

    if pygame.key.get_pressed()[pygame.K_f]:
        packet['L_STICK']['PRESSED'] = True
    
    if pygame.key.get_pressed()[pygame.K_1]:
        packet['DPAD_DOWN'] = True

    if pygame.key.get_pressed()[pygame.K_2]:
        packet['DPAD_UP'] = True

    if pygame.key.get_pressed()[pygame.K_TAB]:
        packet['L'] = True

    if pygame.key.get_pressed()[pygame.K_LSHIFT]:
        packet['ZL'] = True

    if pygame.mouse.get_pressed()[0]:
        packet['ZR'] = True

    if pygame.mouse.get_pressed()[2]:
        packet['R'] = True

    if pygame.key.get_pressed()[pygame.K_e]:
        packet['A'] = True

    if pygame.key.get_pressed()[pygame.K_SPACE]:
        packet['B'] = True

    if pygame.key.get_pressed()[pygame.K_q]:
        packet['X'] = True

    if pygame.key.get_pressed()[pygame.K_z]:
        packet['Y'] = True

    if pygame.key.get_pressed()[pygame.K_r]:
        packet['PLUS'] = True

    screen.fill("purple")

    dx, dy = pygame.mouse.get_rel()
    val_pitch = (0-(dy*mouse_sens_y))%0xFFFF
    val_yaw = (0-(dx*mouse_sens_x))%0xFFFF

    packet['IMU_DATA'][8+((framecount%3)*12)] = val_pitch & 0xFF
    packet['IMU_DATA'][9+((framecount%3)*12)] = (val_pitch >> 8) & 0xFF

    packet['IMU_DATA'][10+((framecount%3)*12)] = val_yaw & 0xFF
    packet['IMU_DATA'][11+((framecount%3)*12)]= (val_yaw >> 8) & 0xFF

    pygame.display.flip()
    
    if framecount%3==0:
        nx.set_controller_input(index, packet)
        packet = nx.create_input_packet()
        packet["IMU_DATA"] = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        if pygame.key.get_focused():
            pygame.mouse.set_pos([600,600])
            pygame.mouse.get_rel()

    framecount = framecount+1
    clock.tick(200)

pygame.quit()

