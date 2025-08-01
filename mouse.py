import pygame
import math
from nxbt import nxbt

pygame.init()

screen_size = 500

screen = pygame.display.set_mode((screen_size,screen_size))
clock = pygame.time.Clock()
running = True

mouse_sens_x = 50
mouse_sens_y = 75
gyro_accel_scaling = 40 #change this if you change mouse_sense_y maybe

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
pygame.mouse.set_visible(False)

camera_y = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if pygame.mouse.get_focused():
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
    else:
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)

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
        packet['DPAD_LEFT'] = True
        packet['A'] = True

    if pygame.key.get_pressed()[pygame.K_2]:
        packet['DPAD_UP'] = True
        packet['A'] = True

    if pygame.key.get_pressed()[pygame.K_3]:
        packet['DPAD_RIGHT'] = True
        packet['A'] = True

    if pygame.key.get_pressed()[pygame.K_4]:
        packet['DPAD_DOWN'] = True
        packet['A'] = True

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
        camera_y = 0
        packet['Y'] = True

    if pygame.key.get_pressed()[pygame.K_x]:
        packet['HOME'] = True

    if pygame.key.get_pressed()[pygame.K_c]:
        packet['CAPTURE'] = True

    if pygame.key.get_pressed()[pygame.K_r]:
        packet['MINUS'] = True

    if pygame.key.get_pressed()[pygame.K_t]:
        packet['PLUS'] = True

    screen.fill("purple")

    dx, dy = pygame.mouse.get_rel()

    camera_y = camera_y - dy

    val_pitch = (0+(dy*mouse_sens_y))%0xFFFF
    val_yaw = (0-(dx*mouse_sens_x))%0xFFFF
    
    #vaguely scale the y position of the cursor with the accepted acc values of the IMU
    val_acc = math.floor(camera_y*(mouse_sens_y/gyro_accel_scaling))

    # Forward-Back axis accelerometer
    packet['IMU_DATA'][0+((framecount%3)*12)] = val_acc & 0xFF
    packet['IMU_DATA'][1+((framecount%3)*12)] = (val_acc >> 8) & 0xFF

    # Left-Right axis accelerometer
    packet['IMU_DATA'][2+((framecount%3)*12)] = 0 & 0xFF
    packet['IMU_DATA'][3+((framecount%3)*12)] = (0 >> 8) & 0xFF

    # Up-Down axis accelerometer
    packet['IMU_DATA'][4+((framecount%3)*12)] = 4100-abs(math.floor(val_acc/2)) & 0xFF
    packet['IMU_DATA'][5+((framecount%3)*12)] = (4100-abs(math.floor(val_acc/2)) >> 8) & 0xFF

    # Up-Down Gyroscope
    packet['IMU_DATA'][8+((framecount%3)*12)] = val_pitch & 0xFF
    packet['IMU_DATA'][9+((framecount%3)*12)] = (val_pitch >> 8) & 0xFF

    # Left-Right Gyroscope
    packet['IMU_DATA'][10+((framecount%3)*12)] = val_yaw & 0xFF
    packet['IMU_DATA'][11+((framecount%3)*12)]= (val_yaw >> 8) & 0xFF

    pygame.display.flip()
    if framecount%3==0:
        nx.set_controller_input(index, packet)
        packet = nx.create_input_packet()
        packet["IMU_DATA"] = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

    framecount = framecount+1
    clock.tick(133)

pygame.quit()