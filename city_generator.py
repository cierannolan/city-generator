import pygame
import random
from PIL import Image, ImageDraw
import colorsys
import os
import datetime


# constants
width, height = 600, 400
minWidth, minHeight = 400, 300
controlPanelHeight = 60
numLayers = 4  # number of building layers
minTopClearance = 40
maxBuildingHeight = height - minTopClearance - 160
absoluteMaxBuildingHeight = 200  # hard maximum for any building height, prevents buildings from being too tall on resize
buildingWidthRange = (30, 100) 

# global variables to store generated elements
originalSkyHsl = None
originalSkyColor = None
originalBuildingColors = None
originalBuildingsData = []
originalMaxBuildingHeight = maxBuildingHeight


def generateSkyColor():
    hue = random.uniform(0, 1)
    saturation = random.uniform(0.1, 0.3)
    brightness = random.uniform(0.2, 0.9)

    r, g, b = colorsys.hls_to_rgb(hue, brightness, saturation)
    
    return (hue, saturation, brightness), (int(r * 255), int(g * 255), int(b * 255))


def generateBuildingColors(hue, saturation, skyBrightness):
    colors = []
    endBrightness = min(0.9, skyBrightness * 1.2) 
    startBrightness = max(0.05, skyBrightness * 0.5)
    brightnessStep = (startBrightness - endBrightness) / (numLayers - 1) if numLayers > 1 else 0
    
    for i in range(numLayers):
        brightness = startBrightness - (i * brightnessStep)
        r, g, b = colorsys.hls_to_rgb(hue, brightness, min(1, saturation * 2))
        colors.append((int(r * 255), int(g * 255), int(b * 255)))
        
    return colors


def drawWindows(draw, x, yTop, width, totalHeight, buildingColor, layerIndex, recordWindows=False):
    r, g, b = buildingColor
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)

    # calculate lit and unlit window colors based on building color
    lightBoost = 0.4 + (layerIndex * 0.1)
    lOn = min(1.0, l + lightBoost)
    sOn = min(1.0, s + 0.3)

    lOff = max(0.3, l * 0.85)
    sOff = max(0.2, s * 0.7)

    wrOn, wgOn, wbOn = colorsys.hls_to_rgb(h, lOn, sOn)
    wrOff, wgOff, wbOff = colorsys.hls_to_rgb(h, lOff, sOff)

    windowColorOn = (int(wrOn * 255), int(wgOn * 255), int(wbOn * 255))
    windowColorOff = (int(wrOff * 255), int(wgOff * 255), int(wbOff * 255))

    # define window grid
    windowSize = 12
    rows = totalHeight // windowSize
    cols = width // windowSize

    # draw each window with 60% chance of being lit
    for row in range(rows):
        for col in range(cols):
            wx = x + col * windowSize + 3
            wy = yTop + row * windowSize + 3
            rect = (wx, wy, wx + 6, wy + 6)
            lit = random.random() < 0.6
            draw.rectangle(rect, fill=windowColorOn if lit else windowColorOff)


def generateBuildingsData(canvasWidth, buildingMaxHeight):
    #generates and saves building data for consistency on resize and refresh buttons
    allLayersData = []
    
    # create buildings for each layer
    for layerIndex in range(numLayers):
        x = 0
        buildings = []
        
        # create buildings across the canvas width
        while x < canvasWidth:
            buildingWidth = random.randint(*buildingWidthRange)
            maxHeight = min(buildingMaxHeight, absoluteMaxBuildingHeight)
            minHeight = max(50, 30 + layerIndex * 15)
            minHeight = min(minHeight, maxHeight - 10)
            
            # vary height based on layer
            if layerIndex == numLayers - 1:
                buildingHeight = random.randint(minHeight, min(maxHeight, height - 20))
            else:
                buildingHeight = random.randint(minHeight, maxHeight)
                
            gap = random.randint(5, 15)  # random gap between buildings
            
            buildings.append({
                'x': x,
                'width': buildingWidth,
                'height': buildingHeight,
                'gap': gap
            })
            
            x += buildingWidth + gap
            
            if x >= canvasWidth:
                break
                
        allLayersData.append(buildings)
    
    return allLayersData


def extendBuildingsData(buildingsData, oldWidth, newWidth, buildingMaxHeight):
    #extends building data on resize
    extendedData = []
    
    for layer in buildingsData:
        extendedLayer = layer.copy()
        lastX = 0
        
        # find where to start adding new buildings
        if layer:
            lastBuilding = layer[-1]
            lastX = lastBuilding['x'] + lastBuilding['width'] + lastBuilding['gap']
        
        x = lastX
        # add buildings until filling the new width
        while x < newWidth:
            buildingWidth = random.randint(*buildingWidthRange)
            layerIndex = buildingsData.index(layer)
            
            maxHeight = min(buildingMaxHeight, absoluteMaxBuildingHeight)
            minHeight = max(50, 30 + layerIndex * 15)
            minHeight = min(minHeight, maxHeight - 10)
            
            if layerIndex == numLayers - 1:
                buildingHeight = random.randint(minHeight, min(maxHeight, height - 20))
            else:
                buildingHeight = random.randint(minHeight, maxHeight)
                
            gap = random.randint(5, 15)
            
            extendedLayer.append({
                'x': x,
                'width': buildingWidth,
                'height': buildingHeight,
                'gap': gap
            })
            
            x += buildingWidth + gap
            
        extendedData.append(extendedLayer)
    
    return extendedData


def drawBuildings(draw, yBase, color, layerIndex, buildings, canvasHeight):
    for building in buildings:
        buildingWidth = building['width']
        buildingHeight = building['height']
        x = building['x']
        
        yTop = yBase - buildingHeight
        xEnd = x + buildingWidth

        if xEnd < x:
            xEnd = x

        draw.rectangle([x, yTop, xEnd, canvasHeight], fill=color)
        drawWindows(draw, x, yTop, buildingWidth, canvasHeight - yTop, color, layerIndex)


def generateCityImage(w, h, refreshColors=False, refreshBuildings=False):
    global originalSkyHsl, originalSkyColor, originalBuildingColors, originalBuildingsData, originalMaxBuildingHeight
    
    # initialize colors and buildings if first run
    if originalSkyHsl is None:
        currentMaxBuildingHeight = min(h - minTopClearance - 160, absoluteMaxBuildingHeight)
        originalMaxBuildingHeight = currentMaxBuildingHeight
        
        originalSkyHsl, originalSkyColor = generateSkyColor()
        originalBuildingColors = generateBuildingColors(*originalSkyHsl)
        originalBuildingsData = generateBuildingsData(w, originalMaxBuildingHeight)
      
    else:
        if refreshColors:
            originalSkyHsl, originalSkyColor = generateSkyColor()
            originalBuildingColors = generateBuildingColors(*originalSkyHsl)
        
        if refreshBuildings:
            currentMaxBuildingHeight = min(h - minTopClearance - 160, absoluteMaxBuildingHeight)
            originalMaxBuildingHeight = currentMaxBuildingHeight
            originalBuildingsData = generateBuildingsData(w, originalMaxBuildingHeight)
            
        # extend buildings if canvas widened
        elif w > width and not refreshBuildings:
            originalBuildingsData = extendBuildingsData(originalBuildingsData, width, w, originalMaxBuildingHeight)

    img = Image.new("RGB", (w, h), originalSkyColor)
    draw = ImageDraw.Draw(img)

    # starting y position for buildings
    yBase = h - (numLayers * 15)

    # draw buildings from back to front (reversed layer order)
    for i in range(numLayers - 1, -1, -1):
        drawBuildings(draw, yBase, originalBuildingColors[i], i, originalBuildingsData[i], h)
        yBase += 20  # difference in height between layers, change for more/less depth effect

    return img


def drawControlPanel(screen, panelRect):
    buttonGrey = (100, 100, 110)
    panelGrey = (80, 80, 85)
    borderGrey = (120, 120, 125)
    
    # draw panel background and border
    pygame.draw.rect(screen, panelGrey, panelRect)
    pygame.draw.rect(screen, borderGrey, panelRect, 2)
    
    buttonWidth = 120
    buttonHeight = 40
    buttonSpacing = 15
    buttonY = panelRect.top + (panelRect.height - buttonHeight) // 2
    
    # center buttons in panel
    totalButtonsWidth = (buttonWidth * 4) + (buttonSpacing * 3)
    startX = panelRect.left + (panelRect.width - totalButtonsWidth) // 2
    
    refreshAllRect = pygame.Rect(startX, buttonY, buttonWidth, buttonHeight)
    refreshColorsRect = pygame.Rect(startX + buttonWidth + buttonSpacing, buttonY, buttonWidth, buttonHeight)
    refreshBuildingsRect = pygame.Rect(startX + 2 * (buttonWidth + buttonSpacing), buttonY, buttonWidth, buttonHeight)
    exportImageRect = pygame.Rect(startX + 3 * (buttonWidth + buttonSpacing), buttonY, buttonWidth, buttonHeight)
    
    pygame.draw.rect(screen, buttonGrey, refreshAllRect)
    pygame.draw.rect(screen, buttonGrey, refreshColorsRect)
    pygame.draw.rect(screen, buttonGrey, refreshBuildingsRect)
    pygame.draw.rect(screen, buttonGrey, exportImageRect)
    
    font = pygame.font.Font(None, 24)
    
    # render text for each button
    textRefreshAll = font.render("Refresh All", True, (255, 255, 255))
    textRectAll = textRefreshAll.get_rect(center=refreshAllRect.center)
    screen.blit(textRefreshAll, textRectAll)
    
    textRefreshColors = font.render("New Colors", True, (255, 255, 255))
    textRectColors = textRefreshColors.get_rect(center=refreshColorsRect.center)
    screen.blit(textRefreshColors, textRectColors)
    
    textRefreshBuildings = font.render("New Buildings", True, (255, 255, 255))
    textRectBuildings = textRefreshBuildings.get_rect(center=refreshBuildingsRect.center)
    screen.blit(textRefreshBuildings, textRectBuildings)
    
    textExportImage = font.render("Export PNG", True, (255, 255, 255))
    textRectExport = textExportImage.get_rect(center=exportImageRect.center)
    screen.blit(textExportImage, textRectExport)
    
    return refreshAllRect, refreshColorsRect, refreshBuildingsRect, exportImageRect


def convertPillowToPygame(pilImg):
    pilImg = pilImg.convert("RGBA")
    mode = pilImg.mode
    size = pilImg.size
    data = pilImg.tobytes()
    return pygame.image.fromstring(data, size, mode)


def exportImage(img):
    # images are saved in exports folder, create exports directory if it doesn't exist
    if not os.path.exists("exports"):
        os.makedirs("exports")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"exports/city_{timestamp}.png"
    img.save(filename)
    return filename


# initialize pygame and create window
pygame.init()
pygame.display.set_caption("Pixel Art City Generator")
initialWidth = width
initialHeight = height
screenWidth = initialWidth
screenHeight = initialHeight + controlPanelHeight
screen = pygame.display.set_mode((screenWidth, screenHeight), pygame.RESIZABLE)

# generate initial image
img = generateCityImage(initialWidth, initialHeight)
pygameImage = convertPillowToPygame(img)


# main game loop
running = True
currentImageWidth = initialWidth
currentImageHeight = initialHeight

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.VIDEORESIZE:
            # handle window resize
            screenWidth = max(event.w, minWidth)
            screenHeight = max(event.h, minHeight + controlPanelHeight)
            screen = pygame.display.set_mode((screenWidth, screenHeight), pygame.RESIZABLE)
            currentImageHeight = screenHeight - controlPanelHeight
            currentImageWidth = screenWidth
            img = generateCityImage(currentImageWidth, currentImageHeight)
            pygameImage = convertPillowToPygame(img)

        if event.type == pygame.MOUSEBUTTONDOWN:
            # handle button clicks
            mouseX, mouseY = pygame.mouse.get_pos()
            panelRect = pygame.Rect(0, currentImageHeight, screenWidth, controlPanelHeight)
            refreshAllRect, refreshColorsRect, refreshBuildingsRect, exportImageRect = drawControlPanel(screen, panelRect)
            
            if refreshAllRect.collidepoint(mouseX, mouseY):
                img = generateCityImage(currentImageWidth, currentImageHeight, 
                refreshColors=True, refreshBuildings=True)
                pygameImage = convertPillowToPygame(img)
            
            elif refreshColorsRect.collidepoint(mouseX, mouseY):
                img = generateCityImage(currentImageWidth, currentImageHeight, 
                refreshColors=True, refreshBuildings=False)
                pygameImage = convertPillowToPygame(img)
                
            elif refreshBuildingsRect.collidepoint(mouseX, mouseY):
                img = generateCityImage(currentImageWidth, currentImageHeight, 
                refreshColors=False, refreshBuildings=True)
                pygameImage = convertPillowToPygame(img)
                
            elif exportImageRect.collidepoint(mouseX, mouseY):
                savedFilename = exportImage(img)
                print(f"Image exported to {savedFilename}")


    screen.fill((50, 50, 55))  # background color
    screen.blit(pygameImage, (0, 0))
    panelRect = pygame.Rect(0, currentImageHeight, screenWidth, controlPanelHeight)
    drawControlPanel(screen, panelRect) 
    pygame.display.flip()  # update display

pygame.quit()