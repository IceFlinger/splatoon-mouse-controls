import pygame
import math
from nxbt import nxbt

pygame.init()
screen = pygame.display.set_mode((1200,1200))
clock = pygame.time.Clock()
running = True

mouse_sens_x = 80
mouse_sens_y = 160
#"BC:9E:BB:F8:71:8C"
switch_addr = ""

nx = nxbt.Nxbt()
index = nx.create_controller(nxbt.PRO_CONTROLLER, reconnect_address=switch_addr)


print("Connecting controller to switch... (Go to Change Grip/Order and trust the switch from bluetoothctl on PC)")
nx.wait_for_connection(index)
print("Connected!")

packet = nx.create_input_packet()
packet["IMU_DATA"] = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

framecount = 0

pygame.event.set_grab(True)

#idk if this even helps tbh
jitter = 3

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
        pygame.mouse.set_visible(False)
        pygame.mouse.set_pos([600,600])
        pygame.mouse.set_visible(True)
        packet['Y'] = True

    if pygame.key.get_pressed()[pygame.K_r]:
        packet['MINUS'] = True

    screen.fill("purple")


    null, ny = pygame.mouse.get_pos()

    dx, dy = pygame.mouse.get_rel()

    val_pitch = (0+(dy*mouse_sens_y))%0xFFFF
    val_yaw = (0-(dx*mouse_sens_x))%0xFFFF

    #vaguely scale the y position of the cursor with the accepted acc values of the IMU
    val_acc = (-(math.floor((-600+ny)*(2.7))))-jitter
    if jitter != -3:
        jitter = -3
    else:
        jitter = 3

    # Forward-Back axis accelerometer
    packet['IMU_DATA'][0+((framecount%3)*12)] = val_acc & 0xFF
    packet['IMU_DATA'][1+((framecount%3)*12)] = (val_acc >> 8) & 0xFF

    # Left-Right axis accelerometer
    packet['IMU_DATA'][2+((framecount%3)*12)] = jitter & 0xFF
    packet['IMU_DATA'][3+((framecount%3)*12)] = (jitter >> 8) & 0xFF

    # Up-Down axis accelerometer
    packet['IMU_DATA'][4+((framecount%3)*12)] = 4100+jitter-abs(math.floor(val_acc/2)) & 0xFF
    packet['IMU_DATA'][5+((framecount%3)*12)] = (4100+jitter-abs(math.floor(val_acc/2)) >> 8) & 0xFF

    # Up-Down Gyroscope
    packet['IMU_DATA'][8+((framecount%3)*12)] = val_pitch+jitter & 0xFF
    packet['IMU_DATA'][9+((framecount%3)*12)] = (val_pitch+jitter >> 8) & 0xFF

    # Left-Right Gyroscope
    packet['IMU_DATA'][10+((framecount%3)*12)] = val_yaw & 0xFF
    packet['IMU_DATA'][11+((framecount%3)*12)]= (val_yaw >> 8) & 0xFF

    pygame.display.flip()
    if framecount%3==0:
        nx.set_controller_input(index, packet)
        packet = nx.create_input_packet()
        packet["IMU_DATA"] = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        if pygame.key.get_focused():
            pygame.mouse.set_visible(False)
            pygame.mouse.set_pos([600,ny])
            pygame.mouse.set_visible(True)
            pygame.mouse.get_rel()

    framecount = framecount+1
    clock.tick(120)

pygame.quit()

