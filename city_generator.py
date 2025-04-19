import pygame
import random
from PIL import Image, ImageDraw
import colorsys

# constants
width, height = 480, 320
num_layers = 4
window_colors = [(255, 255, 200), (255, 255, 100), (200, 200, 150)]
min_top_clearance = 80
max_building_height = height - min_top_clearance - 160
building_width_range = (30, 80)


def generateSkyColor():
    hue = random.uniform(0, 1)
    saturation = random.uniform(0.1, 0.3)
    brightness = random.uniform(0.2, 0.9)

    r, g, b = colorsys.hls_to_rgb(hue, brightness, saturation)
    
    return (hue, saturation, brightness), (int(r * 255), int(g * 255), int(b * 255))


def generateBuildingColors(hue, saturation, sky_brightness):
    colors = []
    base_brightness = sky_brightness * 0.9  
    
    for i in range(num_layers):
        brightness = max(0.05, base_brightness - (i * 0.15)) 
        r, g, b = colorsys.hls_to_rgb(hue, brightness, min(1, saturation * 2))
        colors.append((int(r * 255), int(g * 255), int(b * 255)))
        
    return colors[::-1]


def drawWindows(draw, x, y_top, width, total_height, building_color, layer_index, record_windows=False):
    r, g, b = building_color
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)

    light_boost = 0.4 + (layer_index * 0.1)
    l_on = min(1.0, l + light_boost)
    s_on = min(1.0, s + 0.3)

    l_off = max(0.3, l * 0.85)
    s_off = max(0.2, s * 0.7)

    wr_on, wg_on, wb_on = colorsys.hls_to_rgb(h, l_on, s_on)
    wr_off, wg_off, wb_off = colorsys.hls_to_rgb(h, l_off, s_off)

    window_color_on = (int(wr_on * 255), int(wg_on * 255), int(wb_on * 255))
    window_color_off = (int(wr_off * 255), int(wg_off * 255), int(wb_off * 255))

    window_size = 12
    rows = total_height // window_size
    cols = width // window_size

    for row in range(rows):
        for col in range(cols):
            wx = x + col * window_size + 3
            wy = y_top + row * window_size + 3
            rect = (wx, wy, wx + 6, wy + 6)

            lit = random.random() < 0.6
            draw.rectangle(rect, fill=window_color_on if lit else window_color_off)


def drawBuildings(draw, y_base, color, layer_index, width):
    x = 0
    num_buildings = random.randint(4, 10)
    total_width = 0
    buildings = []

    while x < width:
        building_width = random.randint(*building_width_range)
        buildings.append(building_width)
        total_width += building_width
        x_gap = random.randint(5, 15)

        if total_width + x_gap > width:
            break

        x += building_width + x_gap

    x = 0
    for i, building_width in enumerate(buildings):
        max_height = max_building_height
        min_height = max(50, 30 + layer_index * 15)
        
        min_height = min(min_height, max_height - 10)

        if layer_index == num_layers - 1:
            building_height = random.randint(min_height, min(max_height + 40, height - 20))
        else:
            building_height = random.randint(min_height, max_height)

        if x + building_width > width:
            building_width = width - x

        y_top = y_base - building_height
        x_end = x + building_width

        if x_end < x:
            x_end = x

        draw.rectangle([x, y_top, x_end, height], fill=color)
        drawWindows(draw, x, y_top, building_width, height - y_top, color, layer_index, record_windows=True)

        x += building_width + random.randint(5, 15)


def generateCityImage(w, h):
    max_building_height = h - min_top_clearance - 160
    
    sky_hsl, sky_color = generateSkyColor()
    building_colors = generateBuildingColors(*sky_hsl)

    img = Image.new("RGB", (w, h), sky_color)
    draw = ImageDraw.Draw(img)

    y_base = h - (num_layers * 15)

    for i in range(num_layers - 1, -1, -1):
        drawBuildings(draw, y_base, building_colors[i], i, w)
        y_base += 20

    return img, sky_hsl


def drawRefreshButton(screen):
    button_color = (100, 150, 255)
    button_rect = pygame.Rect(10, 10, 100, 40)
    pygame.draw.rect(screen, button_color, button_rect)
    font = pygame.font.Font(None, 36)
    text = font.render("Refresh", True, (255, 255, 255))
    screen.blit(text, (button_rect.x + 5, button_rect.y + 5))

    return button_rect


def convertPillowToPygame(pil_img):
    pil_img = pil_img.convert("RGBA")
    mode = pil_img.mode
    size = pil_img.size
    data = pil_img.tobytes()
    return pygame.image.fromstring(data, size, mode)

pygame.init()
screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
pygame.display.set_caption("pixel art city generator demo")

img, sky_hsl = generateCityImage(width, height)
pygame_image = convertPillowToPygame(img)


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.VIDEORESIZE:
            width, height = event.w, event.h
            img, sky_hsl = generateCityImage(width, height)
            pygame_image = convertPillowToPygame(img)

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            button_rect = drawRefreshButton(screen)

            if button_rect.collidepoint(mouse_x, mouse_y):
                img, sky_hsl = generateCityImage(width, height)
                pygame_image = convertPillowToPygame(img)

    pygame_image = convertPillowToPygame(img)
    screen.fill((255, 255, 255))
    screen.blit(pygame_image, (0, 0))
    drawRefreshButton(screen)
    pygame.display.flip()

pygame.quit()