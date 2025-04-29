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
maxBuildingHeight = height - minTopClearance - 120
absoluteMaxBuildingHeight = 200  # hard maximum for any building height, prevents buildings from being too tall on resize
buildingWidthRange = (40, 100)
litWindowRate = 0.4

roofLightChance = 0.2  # chance of a building having roof lights
roofLightColors = [(255, 0, 0), (0, 255, 0), (255, 255, 0)]  # red, green, yellow
roofLightSize = 3
roofLightSpacing = 12
roofLightHeight = 1  # height above building roof
skyBrightnessDarkThreshold = 0.45  # threshold below which sky is considered "dark" enough for roof lights

originalSkyHsl = None
originalSkyColor = None
originalBuildingColors = None
originalBuildingsData = []
originalMaxBuildingHeight = maxBuildingHeight
windowsData = {}  # store window data for each building
currentRoofLightColor = None
isSkyDark = False  # track if sky is dark enough for roof lights


def generateSkyColor():
    global isSkyDark
    
    hue = random.uniform(0, 1)
    saturation = random.uniform(0.1, 0.3)
    brightness = random.uniform(0.2, 0.9)
    
    isSkyDark = brightness < skyBrightnessDarkThreshold

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


def drawWindows(draw, x, yTop, width, totalHeight, buildingColor, layerIndex, buildingId=None):
    global windowsData
    
    # if none is provided, generate a building id - stores roof lights and window data for each building
    if buildingId is None:
        buildingId = f"b_{x}_{yTop}_{width}_{totalHeight}_{layerIndex}"
    
    # if building already has window data, use it. otherwise create a new object
    if buildingId in windowsData:
        windowInfo = windowsData[buildingId]
        windowStyle = windowInfo['style']
        windowPositions = windowInfo['positions']
    else:
        windowStyle = random.choices( 
            ["normal", "wide", "tall", "tall-inverse"], 
            weights=[0.8, 0.02, 0.18, 0.09], 
            k=1
        )[0]
        
        windowPositions = []
        windowsData[buildingId] = {
            'style': windowStyle,
            'positions': windowPositions
        }
    
    # calculate lit and unlit window colours based on building color
    r, g, b = buildingColor
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    
    lightBoost = 0.35 + (layerIndex * 0.05)
    lOn = min(0.95, l + lightBoost)
    sOn = min(1.0, s + 0.3)

    lOff = max(0.3, l * 0.85)
    sOff = max(0.2, s * 0.7)

    wrOn, wgOn, wbOn = colorsys.hls_to_rgb(h, lOn, sOn)
    wrOff, wgOff, wbOff = colorsys.hls_to_rgb(h, lOff, sOff)

    windowColorOn = (int(wrOn * 255), int(wgOn * 255), int(wbOn * 255))
    windowColorOff = (int(wrOff * 255), int(wgOff * 255), int(wbOff * 255))
    
    if windowStyle == "wide":
        windowHeight = 4
        windowWidth = width - 10
        minWindowSpacing = 6  # vertical space between windows
        
        # calculate how many windows can fit
        maxRows = (totalHeight - minWindowSpacing) // (windowHeight + minWindowSpacing)
        maxRows = max(1, maxRows)
        
        # calculate spacing to distribute windows evenly vertically
        totalWindowHeightSpace = maxRows * windowHeight
        vertSpacing = (totalHeight - totalWindowHeightSpace) / (maxRows + 1)
        
        # generate positioning if needed
        if not windowsData[buildingId]['positions']:
            for row in range(maxRows):
                lit = random.random() < litWindowRate
                windowsData[buildingId]['positions'].append(lit)
        
        # draw windows using stored positions
        for row in range(maxRows):
            wx = x + 4  # 4px clearance from left edge
            wy = yTop + vertSpacing + row * (windowHeight + vertSpacing)
            rect = (wx, wy, wx + windowWidth, wy + windowHeight)
            
            if row < len(windowsData[buildingId]['positions']):
                lit = windowsData[buildingId]['positions'][row]
            else:
                lit = random.random() < litWindowRate
                windowsData[buildingId]['positions'].append(lit)
                
            draw.rectangle(rect, fill=windowColorOn if lit else windowColorOff)
            
    elif windowStyle == "tall":
        windowWidth = 6
        windowHeight = 12
        minWindowSpacing = 6
        
        maxCols = (width - minWindowSpacing) // (windowWidth + minWindowSpacing)
        maxRows = (totalHeight - minWindowSpacing) // (windowHeight + minWindowSpacing)
        
        maxCols = max(1, maxCols)
        maxRows = max(1, maxRows)
        
        totalWindowWidthSpace = maxCols * windowWidth
        totalWindowHeightSpace = maxRows * windowHeight
        
        horizSpacing = (width - totalWindowWidthSpace) / (maxCols + 1)
        vertSpacing = (totalHeight - totalWindowHeightSpace) / (maxRows + 1)
        
        if not windowsData[buildingId]['positions']:
            for row in range(maxRows):
                row_lights = []
                for col in range(maxCols):
                    lit = random.random() < litWindowRate
                    row_lights.append(lit)
                windowsData[buildingId]['positions'].append(row_lights)
        
        for row in range(maxRows):
            for col in range(maxCols):
                wx = x + horizSpacing + col * (windowWidth + horizSpacing)
                wy = yTop + vertSpacing + row * (windowHeight + vertSpacing)
                
                # changes how far up the divider is in the window
                dividerY = wy + int(windowHeight * 0.25)
                
                # if row and column exist in data, get lit status
                if row < len(windowsData[buildingId]['positions']) and col < len(windowsData[buildingId]['positions'][row]):
                    lit = windowsData[buildingId]['positions'][row][col]
                else:
                    lit = random.random() < litWindowRate
                    
                    while row >= len(windowsData[buildingId]['positions']):
                        windowsData[buildingId]['positions'].append([])
                        
                    while col >= len(windowsData[buildingId]['positions'][row]):
                        windowsData[buildingId]['positions'][row].append(False)
                        
                    windowsData[buildingId]['positions'][row][col] = lit
                
                windowColor = windowColorOn if lit else windowColorOff
                
                upperRect = (wx, wy, wx + windowWidth, dividerY - 1)
                draw.rectangle(upperRect, fill=windowColor)
                
                # change value here to increase divider by decreasing the window's larger half's height
                lowerRect = (wx, dividerY + 3, wx + windowWidth, wy + windowHeight)
                draw.rectangle(lowerRect, fill=windowColor)
    
    elif windowStyle == "tall-inverse":
        windowWidth = 6
        windowHeight = 12
        minWindowSpacing = 6
        
        maxCols = (width - minWindowSpacing) // (windowWidth + minWindowSpacing)
        maxRows = (totalHeight - minWindowSpacing) // (windowHeight + minWindowSpacing)
        
        maxCols = max(1, maxCols)
        maxRows = max(1, maxRows)
        
        totalWindowWidthSpace = maxCols * windowWidth
        totalWindowHeightSpace = maxRows * windowHeight
        
        horizSpacing = (width - totalWindowWidthSpace) / (maxCols + 1)
        vertSpacing = (totalHeight - totalWindowHeightSpace) / (maxRows + 1)
        
        if not windowsData[buildingId]['positions']:
            for row in range(maxRows):
                row_lights = []
                for col in range(maxCols):
                    lit = random.random() < litWindowRate
                    row_lights.append(lit)
                windowsData[buildingId]['positions'].append(row_lights)
        
        for row in range(maxRows):
            for col in range(maxCols):
                wx = x + horizSpacing + col * (windowWidth + horizSpacing)
                wy = yTop + vertSpacing + row * (windowHeight + vertSpacing)
                
                # changes how far up the divider is in the window
                dividerY = wy + int(windowHeight * 0.75)
                
                if row < len(windowsData[buildingId]['positions']) and col < len(windowsData[buildingId]['positions'][row]):
                    lit = windowsData[buildingId]['positions'][row][col]
                else:
                    lit = random.random() < litWindowRate
                    
                    while row >= len(windowsData[buildingId]['positions']):
                        windowsData[buildingId]['positions'].append([])
                        
                    while col >= len(windowsData[buildingId]['positions'][row]):
                        windowsData[buildingId]['positions'][row].append(False)
                        
                    windowsData[buildingId]['positions'][row][col] = lit
                
                windowColor = windowColorOn if lit else windowColorOff
                
                # change value here to increase divider by decreasing the window's larger half's height
                upperRect = (wx, wy, wx + windowWidth, dividerY - 3)
                draw.rectangle(upperRect, fill=windowColor)
                

                lowerRect = (wx, dividerY + 1, wx + windowWidth, wy + windowHeight)
                draw.rectangle(lowerRect, fill=windowColor)

    else:  # normal windows
        windowWidth = 6
        windowHeight = 6
        minWindowSpacing = 6
        
        maxCols = (width - minWindowSpacing) // (windowWidth + minWindowSpacing)
        maxRows = (totalHeight - minWindowSpacing) // (windowHeight + minWindowSpacing)
        
        maxCols = max(1, maxCols)
        maxRows = max(1, maxRows)
        
        totalWindowWidthSpace = maxCols * windowWidth
        totalWindowHeightSpace = maxRows * windowHeight
        
        horizSpacing = (width - totalWindowWidthSpace) / (maxCols + 1)
        vertSpacing = (totalHeight - totalWindowHeightSpace) / (maxRows + 1)
        
        if not windowsData[buildingId]['positions']:
            for row in range(maxRows):
                row_lights = []
                for col in range(maxCols):
                    lit = random.random() < litWindowRate
                    row_lights.append(lit)
                windowsData[buildingId]['positions'].append(row_lights)
        
        for row in range(maxRows):
            for col in range(maxCols):
                wx = x + horizSpacing + col * (windowWidth + horizSpacing)
                wy = yTop + vertSpacing + row * (windowHeight + vertSpacing)
                rect = (wx, wy, wx + windowWidth, wy + windowHeight)
                
                if row < len(windowsData[buildingId]['positions']) and col < len(windowsData[buildingId]['positions'][row]):
                    lit = windowsData[buildingId]['positions'][row][col]
                else:
                    lit = random.random() < litWindowRate

                    while row >= len(windowsData[buildingId]['positions']):
                        windowsData[buildingId]['positions'].append([])
                        
                    while col >= len(windowsData[buildingId]['positions'][row]):
                        windowsData[buildingId]['positions'][row].append(False)
                        
                    windowsData[buildingId]['positions'][row][col] = lit
                
                draw.rectangle(rect, fill=windowColorOn if lit else windowColorOff)
    
    return buildingId


def addRoofLights(draw, x, width, yTop, buildingId=None):
    # if building already has roof light data, use it, otherwise decide if building will have roof it
    global currentRoofLightColor, isSkyDark

    if not isSkyDark:
        return

    if buildingId is None:
        buildingId = f"r_{x}_{yTop}_{width}"

    if buildingId in windowsData and 'roofLights' in windowsData[buildingId]:
        roofLightInfo = windowsData[buildingId]['roofLights']
        hasLights = roofLightInfo['hasLights']
        lightPositions = roofLightInfo['positions']
    else:
        hasLights = random.random() < roofLightChance
        lightPositions = []
        
        if buildingId not in windowsData:
            windowsData[buildingId] = {}
        
        windowsData[buildingId]['roofLights'] = {
            'hasLights': hasLights,
            'positions': lightPositions
        }
    
    if not hasLights:
        return
    
    # calculate how many lights can fit on the roof
    maxLights = (width - roofLightSize) // (roofLightSize + roofLightSpacing)
    
    if not lightPositions:
        totalLightsWidth = maxLights * roofLightSize + (maxLights - 1) * roofLightSpacing
        startX = x + (width - totalLightsWidth) // 2
        
        for i in range(maxLights):
            lightX = startX + i * (roofLightSize + roofLightSpacing)
            lightPositions.append(lightX)
        
        windowsData[buildingId]['roofLights']['positions'] = lightPositions
    
    for lightX in lightPositions:
        light_rect = (lightX, yTop - roofLightHeight - roofLightSize, 
                     lightX + roofLightSize, yTop - roofLightHeight)
        draw.rectangle(light_rect, fill=currentRoofLightColor)


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
            
            buildingId = f"b_{x}_{layerIndex}_{buildingWidth}_{buildingHeight}"
            
            buildings.append({
                'x': x,
                'width': buildingWidth,
                'height': buildingHeight,
                'gap': gap,
                'id': buildingId
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
            
            buildingId = f"b_{x}_{layerIndex}_{buildingWidth}_{buildingHeight}"
            
            extendedLayer.append({
                'x': x,
                'width': buildingWidth,
                'height': buildingHeight,
                'gap': gap,
                'id': buildingId
            })
            
            x += buildingWidth + gap
            
        extendedData.append(extendedLayer)
    
    return extendedData


def drawBuildings(draw, yBase, color, layerIndex, buildings, canvasHeight):
    for building in buildings:
        buildingWidth = building['width']
        buildingHeight = building['height']
        x = building['x']
        buildingId = building.get('id')
        
        yTop = yBase - buildingHeight
        xEnd = x + buildingWidth

        if xEnd < x:
            xEnd = x

        draw.rectangle([x, yTop, xEnd, canvasHeight], fill=color)
        
        # draw windows and store buildingId for future reference
        windowBuildingId = drawWindows(draw, x, yTop, buildingWidth, canvasHeight - yTop, color, layerIndex, buildingId)
        
        # update the building's ID if it was generated in drawWindows
        if not buildingId:
            building['id'] = windowBuildingId
        
        addRoofLights(draw, x, buildingWidth, yTop, buildingId)


def generateCityImage(w, h, refreshColors=False, refreshBuildings=False):
    global originalSkyHsl, originalSkyColor, originalBuildingColors, originalBuildingsData, originalMaxBuildingHeight, windowsData, currentRoofLightColor, isSkyDark

    # initialize colours and buildings if first run
    if originalSkyHsl is None:
        currentMaxBuildingHeight = min(h - minTopClearance - 160, absoluteMaxBuildingHeight)
        originalMaxBuildingHeight = currentMaxBuildingHeight

        originalSkyHsl, originalSkyColor = generateSkyColor()
        originalBuildingColors = generateBuildingColors(*originalSkyHsl)
        originalBuildingsData = generateBuildingsData(w, originalMaxBuildingHeight)
        # sets roof light colour for the image
        currentRoofLightColor = random.choice(roofLightColors)

    else:
        if refreshColors:
            originalSkyHsl, originalSkyColor = generateSkyColor()
            originalBuildingColors = generateBuildingColors(*originalSkyHsl)
            currentRoofLightColor = random.choice(roofLightColors)
            
            print(originalSkyHsl[2])
            isSkyDark = originalSkyHsl[2] < skyBrightnessDarkThreshold  

        if refreshBuildings:
            currentMaxBuildingHeight = min(h - minTopClearance - 120, absoluteMaxBuildingHeight)
            originalMaxBuildingHeight = currentMaxBuildingHeight
            originalBuildingsData = generateBuildingsData(w, originalMaxBuildingHeight)
            # reset windows data when buildings are refreshed
            windowsData = {}
            currentRoofLightColor = random.choice(roofLightColors)

        elif w > width and not refreshBuildings:
            originalBuildingsData = extendBuildingsData(originalBuildingsData, width, w, originalMaxBuildingHeight)

    img = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # sky drawing section

    # original color
    base_r, base_g, base_b = originalSkyColor
    base_h, base_l, base_s = colorsys.rgb_to_hls(base_r / 255, base_g / 255, base_b / 255)

    darker_l = max(0.0, base_l * 0.8)  # darkest gradient point
    darker_r, darker_g, darker_b = colorsys.hls_to_rgb(base_h, darker_l, base_s)
    darker_color = (int(darker_r * 255), int(darker_g * 255), int(darker_b * 255))

    gradient_start_y = int(h * 0.25)  # sky gradient start point
    draw.rectangle([(0, gradient_start_y), (w, h)], fill=originalSkyColor)

    gradient_height = gradient_start_y
    num_bands = max(1, gradient_height // 20)  # increase for less gradient bands
    band_height = gradient_height / num_bands

    for band in range(int(num_bands)):
        ratio = band / (num_bands - 1) if num_bands > 1 else 0

        #decrease the r,g,b value
        r = int(base_r + (darker_color[0] - base_r) * ratio) 
        g = int(base_g + (darker_color[1] - base_g) * ratio)
        b = int(base_b + (darker_color[2] - base_b) * ratio)

        y_start = int(gradient_start_y - (band + 1) * band_height)
        y_end = int(gradient_start_y - band * band_height)

        draw.rectangle([(0, max(0, y_start)), (w, max(0, y_end))], fill=(r, g, b))

    # building drawing 

    yBase = h - (numLayers * 15)

    for i in range(numLayers - 1, -1, -1):
        drawBuildings(draw, yBase, originalBuildingColors[i], i, originalBuildingsData[i], h)
        yBase += 20

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
    
    textRefreshColors = font.render("New Colours", True, (255, 255, 255))
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
                windowsData = {}
                img = generateCityImage(currentImageWidth, currentImageHeight, 
                refreshColors=True, refreshBuildings=True)
                pygameImage = convertPillowToPygame(img)
            
            elif refreshColorsRect.collidepoint(mouseX, mouseY):
                img = generateCityImage(currentImageWidth, currentImageHeight, 
                refreshColors=True, refreshBuildings=False)
                pygameImage = convertPillowToPygame(img)
                
            elif refreshBuildingsRect.collidepoint(mouseX, mouseY):
                windowsData = {}
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