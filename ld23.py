import pygame, sys, math, random
from pygame.locals import *

from Utils import Vec2d

SCALE = 3
DEBUG = False
SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
COLORKEY = (121, 0, 255)
BLOCKED_KEY = (255, 0, 0, 255)
PLAYER_KEY = (0, 0, 255, 255)
CENTIPEDE_KEY = (130, 0, 0, 255)
CATERPILAR_KEY = (130, 121, 0, 255)
PILLBUG_KEY = (69, 69, 69, 255)
TRIGGER_KEY = (255, 0, 215, 255)
BOUNDING_TYPES = {
        'HEAD': (32, 0, 32, 10),
        'RIGHT': (53, 32, 21, 58),
        'LEFT': (21, 32, 21, 58),
        'FEET': (32, 85, 32, 10),
        '_LEFT': (11, 64, 21, 21),
        '_RIGHT': (64, 64, 21, 21),
        }
ENEMY_TYPES = {
        'CATERPILAR': {
            'HIT': (42, 0, 96, 53),
            'LEFT': (11, 64, 21, 21),
            'RIGHT': (64, 64, 21, 21),
            'SPEED': 96,
            'ANIM': (
                (
                    (0,2), (1,2), (2,2)
                    ), 
                (
                    (0,3), (1,3), (2,3)
                    )
                ),
            },
        'CENTIPEDE': {
            'HIT': (21, 10, 53, 75),
            'LEFT': (11, 64, 21, 21),
            'RIGHT': (64, 64, 21, 21),
            'SPEED': 96*2,
            'ANIM': (
                (
                    (0,0), (1,0), (2,0)
                    ), 
                (
                    (0,1), (1,1), (2,1)
                    )
                ),
            },
        }

class SpriteSheet(object):
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert()
        except pygame.error, message:
            raise SystemExit, message

    def imageAt(self, offset):
        offsetX = offset[0]*32
        offsetY = offset[1]*32
        myOffset = [offsetX, offsetY, 31, 31]
        rect = pygame.Rect(myOffset)
        image = pygame.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        image.set_colorkey(COLORKEY, pygame.RLEACCEL)
        return pygame.transform.scale(image, (32*SCALE, 32*SCALE))

    def getSlice(self, sliceRect):
        rect = pygame.Rect(sliceRect)
        image = pygame.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        image.set_colorkey(COLORKEY, pygame.RLEACCEL)
        return pygame.transform.scale(image, (rect.width*SCALE, rect.height*SCALE))

class BoundingBox(pygame.sprite.Sprite):
    def __init__(self, position, boundingType, debug=DEBUG):
        pygame.sprite.Sprite.__init__(self)
        self.debug = debug
        self.position = position
        self.rectInfo = BOUNDING_TYPES[boundingType]
        self.name = boundingType
        self.update(self.position)
    
    def update(self, position):
        x = self.position[0]
        y = self.position[1]
        self.rect = pygame.Rect(x+self.rectInfo[0], y+self.rectInfo[1], self.rectInfo[2], self.rectInfo[3])

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position, enemyType, triggerGroup, debug=DEBUG):
        pygame.sprite.Sprite.__init__(self)
        self.sheet = SpriteSheet("entitySheet.png")
        self.mapPart = 0
        self.debug = debug
        self.position = position
        self.triggerGroup = triggerGroup
        self.triggerBoxes = pygame.sprite.Group()
        self.initTriggerBoxes()
        self.time = 0.0
        self.direction = 1
        self.frame = 0
        self.pauseTime = 2.0
        self.enemyType = ENEMY_TYPES[enemyType]
        self.speed = self.enemyType['SPEED']
        self.stopped = self.standing = False
        self.standingRight = self.sheet.imageAt((self.enemyType['ANIM'][0][0]))
        self.standingLeft = self.sheet.imageAt((self.enemyType['ANIM'][1][0]))
        self.movingRight = (
                self.sheet.imageAt((self.enemyType['ANIM'][0][1])),
                self.sheet.imageAt((self.enemyType['ANIM'][0][2]))
                )
        self.movingLeft = (
                self.sheet.imageAt((self.enemyType['ANIM'][1][1])),
                self.sheet.imageAt((self.enemyType['ANIM'][1][2]))
                )
        self.image = self.standingRight
        self.update(0, 0)
    
    def initTriggerBoxes(self):
        leftTrigger = BoundingBox(self.position, '_LEFT')
        rightTrigger = BoundingBox(self.position, '_RIGHT')
        self.triggerBoxes.add(leftTrigger)
        self.triggerBoxes.add(rightTrigger)

    def update(self, offset, sTime):
        if offset != None:
            if offset > self.mapPart:
                self.mapPart = offset
                self.rect = self.rect.move(-SCREEN_WIDTH, 0)
                self.position[0]-=SCREEN_WIDTH
            elif offset < self.mapPart:
                self.mapPart = offset
                self.rect = self.rect.move(SCREEN_WIDTH, 0)
                self.position[0]+=SCREEN_WIDTH

        self.time+=sTime
        if not self.stopped and self.pauseTime <= -10.0:
            action = random.randrange(1, 100, 1)
            if action % 25 == 0:
                self.pauseTime = random.randrange(1, 5, 1)
                self.stopped = True
        else:
            self.pauseTime-=sTime

        if not self.stopped:
            if sTime > 0:
                self.position[0]+=self.speed*sTime*self.direction

        x = self.position[0]
        y = self.position[1]
        self.rect = pygame.Rect(x+self.enemyType['HIT'][0], y+self.enemyType['HIT'][1], self.enemyType['HIT'][2], self.enemyType['HIT'][3])

        self.triggerBoxes.update(self.position)

        checkCollisions = pygame.sprite.groupcollide(self.triggerBoxes, self.triggerGroup, False, False)
        collisionTypes = [sprite.name for sprite in checkCollisions]
        if len(collisionTypes) > 0:
            self.direction*=-1

        if self.direction > 0:
            self.standing = self.standingRight
        else:
            self.standing = self.standingLeft

        if not self.stopped:
            if self.direction > 0:
                self.image = self.movingRight[self.frame]
            else: 
                self.image = self.movingLeft[self.frame]
        else:
            self.image = self.standing
            self.pauseTime-=sTime
            if self.pauseTime < 0:
                self.stopped = False

        if self.time > .15:
            self.time = 0.0
            if self.frame == 0:
                self.frame = 1
            else:
                self.frame = 0

class BackgroundBlock(pygame.sprite.Sprite):
    def __init__(self, position, debug=DEBUG):
        pygame.sprite.Sprite.__init__(self)
        self.mapPart = 0
        self.debug = debug
        self.position = position
        self.rect = pygame.Rect(
                self.position[0],
                self.position[1],
                96,
                96,
                )
        self.image = pygame.Surface((self.rect.size)).convert()
        self.image.fill((0, 0, 0), self.rect)
        self.image.set_alpha(125)

    def update(self, offset):
        if offset > self.mapPart:
            self.mapPart = offset
            self.rect = self.rect.move(-SCREEN_WIDTH, 0)
        elif offset < self.mapPart:
            self.mapPart = offset
            self.rect = self.rect.move(SCREEN_WIDTH, 0)

class Blocked(pygame.sprite.Sprite):
    def __init__(self, position, debug=DEBUG):
        pygame.sprite.Sprite.__init__(self)
        self.mapPart = 0
        self.debug = debug
        self.position = position
        self.rect = pygame.Rect(
                self.position[0],
                self.position[1],
                96,
                96,
                )
    
    def update(self, offset):
        if offset > self.mapPart:
            self.mapPart = offset
            self.rect = self.rect.move(-SCREEN_WIDTH, 0)
        elif offset < self.mapPart:
            self.mapPart = offset
            self.rect = self.rect.move(SCREEN_WIDTH, 0)

class Map():
    def __init__(self, mapName='game', debug=DEBUG):
        self.debug = debug
        self.position = Vec2d(0, 0)
        self.startLocation = False
        self.platform = self.scaleUp(pygame.image.load('%sPlatform.png' % mapName).convert())
        self.platform.set_colorkey(COLORKEY, pygame.RLEACCEL)
        self.backgroundLayer = self.scaleUp(pygame.image.load('%sBackground.png' % mapName).convert())
        self.backgroundLayer.set_colorkey(COLORKEY, pygame.RLEACCEL)
        self.platform.blit(self.backgroundLayer, (0, 0))
        
        self.triggerGroup = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.ending = pygame.sprite.Group()
        #self.pillBugs = pygame.sprite.Group()

        self.spriteLayer = self.scaleUp(pygame.image.load('%sSpriteMap.png' % mapName).convert())
        self.blocked = pygame.sprite.Group()
        self.initSprites()
        self.gameTime = 100.0

        if self.debug:
            for item in self.blocked:
                pygame.draw.rect(self.platform, (255, 0, 0), item.rect, 1)
                pygame.draw.line(
                        self.platform, 
                        (255, 0, 0), 
                        (item.rect[0], item.rect[1]), 
                        (item.rect[0]+item.rect[2], item.rect[1]+item.rect[3]), 
                        1,
                        )
                pygame.draw.line(
                        self.platform,
                        (255, 0, 0),
                        (item.rect[0]+item.rect[2], item.rect[1]),
                        (item.rect[0], item.rect[1]+item.rect[3]),
                        1,
                        )

        self.moveLeft = self.moveRight = False
        self.time = 0.0
        self.speed = 96*4
        self.offset = 0
        
        self.myImage = self.mapPiece(0)

    def tileType(self, offset, sheet):
        offsetX = offset[0]*96
        offsetY = offset[1]*96
        myOffset = [offsetX, offsetY, 95, 95]
        rect = pygame.Rect(myOffset)
        image = pygame.Surface(rect.size).convert()
        image.blit(sheet, (0, 0), rect)
        image.set_colorkey(COLORKEY, pygame.RLEACCEL)
        thisColor = image.get_at((96/2, 96/2))
        if self.debug:
            if thisColor != (0, 0, 19, 255):
                print thisColor
        return image.get_at((96/2, 96/2))

    def initSprites(self):
        sizeX = int(self.spriteLayer.get_width() / 96.)
        sizeY = int(self.spriteLayer.get_height() / 96.)
        for i in range(sizeY):
            for j in range(sizeX):
                if self.tileType((j, i), self.spriteLayer) == BLOCKED_KEY:
                    self.blocked.add(Blocked(Vec2d(j*96, i*96)))
                elif self.tileType((j, i), self.spriteLayer) == PLAYER_KEY:
                    self.startLocation = (j*96, i*96)
                elif self.tileType(Vec2d(j, i), self.spriteLayer) == CATERPILAR_KEY:
                    self.enemies.add(Enemy(Vec2d(j*96, i*96), 'CATERPILAR', self.triggerGroup))
                elif self.tileType((j, i), self.spriteLayer) == TRIGGER_KEY:
                    self.triggerGroup.add(Blocked(Vec2d(j*96, i*96)))
                elif self.tileType((j, i), self.spriteLayer) == CENTIPEDE_KEY:
                    self.enemies.add(Enemy(Vec2d(j*96, i*96), 'CENTIPEDE', self.triggerGroup))
                elif self.tileType((j, i), self.spriteLayer) == PILLBUG_KEY:
                    self.ending.add(Blocked(Vec2d(j*96, i*96)))

    def mapPiece(self, offset):
        offset = (SCREEN_WIDTH)*offset
        rect = pygame.Rect(
                self.position[0]+offset,
                self.position[1],
                SCREEN_WIDTH*SCALE,
                SCREEN_HEIGHT*SCALE
                )
        thisPiece = pygame.Surface(rect.size).convert()
        thisPiece.set_colorkey(COLORKEY, pygame.RLEACCEL)
        thisPiece.blit(self.platform, (0, 0), rect)
        self.enemies.update(offset, 0.0)
        return thisPiece

    def scaleUp(self, image):
        return pygame.transform.scale(
                image, 
                (image.get_width()*3, image.get_height()*3)
                )

    def update(self, sTime):
        if self.moveRight:
            self.offset += 1
            self.blocked.update(self.offset)
            self.myImage = self.mapPiece(self.offset)
        if self.moveLeft:
            self.offset -= 1
            self.blocked.update(self.offset)
            self.myImage = self.mapPiece(self.offset)
        self.enemies.update(None, sTime)
        self.triggerGroup.update(self.offset)
        self.gameTime-=sTime

    def draw(self):
        return self.myImage

class Player(pygame.sprite.Sprite):
    def __init__(self, position, enemyGroup, debug=DEBUG):
        pygame.sprite.Sprite.__init__(self)
        self.debug = debug
        self.sheet = SpriteSheet("playerSheet.png") 
        self.standRight = self.sheet.imageAt((0,0))
        self.standLeft = self.sheet.imageAt((0,1))
        self.standing = self.standRight
        self.moveLeft = self.moveRight = self.fall = self.jumping = self.moving = self.hitRecently = False
        self.speed = 96*4
        self.time = 0.0
        self.vector = Vec2d(0, 0)
        self.health = 6
        self.enemyGroup = enemyGroup
        self.Heart = self.sheet.imageAt((0,4))
        self.halfHeart = self.sheet.imageAt((1,4))
        self.runningRight = (
                self.sheet.imageAt((1,0)),
                self.sheet.imageAt((2,0)),
                self.sheet.imageAt((3,0)),
                )
        self.runningLeft = (
                self.sheet.imageAt((1,1)),
                self.sheet.imageAt((2,1)),
                self.sheet.imageAt((3,1)),
                )
        self.fallingRight = (
                self.sheet.imageAt((0,2)),
                self.sheet.imageAt((1,2)),
                )
        self.fallingLeft = (
                self.sheet.imageAt((0,3)),
                self.sheet.imageAt((1,3)),
                )
        self.image = self.sheet.imageAt((0,0))

        self.boundingBoxes = pygame.sprite.Group()
        self.position = Vec2d(position)
        self.initBoundingBoxes()
        self.updateRect()

        self.fallAnimation = 0
        self.runAnimation = 0
        self.direction = 1

    def drawHealth(self):
        panelPos = (0, 0)
        wholeHearts = int(self.health / 2)
        halfHearts = (self.health % 2)
        heartPanel = pygame.Surface((96*3, 96)).convert()
        heartPanel.fill(COLORKEY)
        heartPanel.set_colorkey(COLORKEY, pygame.RLEACCEL)
        for i in range(wholeHearts):
            heartPanel.blit(self.Heart, (i*96, 0))
            panelPos = (i*96+96, 0)
        if halfHearts:
            heartPanel.blit(self.halfHeart, panelPos)
        return heartPanel

    def initBoundingBoxes(self):
        for boundingType in BOUNDING_TYPES:
            thisSprite = BoundingBox(self.position, boundingType)
            self.boundingBoxes.add(thisSprite)

    def draw(self):
        if self.debug:
            pygame.draw.rect(self.image, (255, 0, 0), self.rect, 1)
        return self.image

    def updateRect(self):
        x = self.position[0]
        y = self.position[1]
        self.rect = pygame.Rect(x+32, y, 32, 96)
        self.boundingBoxes.update(self.position)

    def jump(self):
        if self.jumping:
            pass
        else:
            self.jumping = True
            self.position[1]-=5
            self.updateRect()
            self.vector[1]-=1200

    def handleHit(self):
        self.health-=1
        self.hitRecently = 1.0

    def update(self, sTime, blockedTiles):
        blockedLeft = blockedRight = blockedTop = onGround = False
        self.time+=sTime

        groupCollisions = pygame.sprite.groupcollide(self.boundingBoxes, blockedTiles, False, False)
        collisionTypes = [sprite.name for sprite in groupCollisions]
        if 'FEET' in collisionTypes:
            self.vector[1] = 0
            self.jumping = False
            onGround = True
        if 'LEFT' in collisionTypes:
            if self.vector[0] < 0:
                self.vector[0] = 0
            blockedLeft = True
        if 'RIGHT' in collisionTypes:
            if self.vector[0] > 0:
                self.vector[0] = 0
            blockedRight = True
        if 'HEAD' in collisionTypes:
            self.vector[1] = 0
            blockedTop = True

        enemyCollisions = pygame.sprite.spritecollide(self, self.enemyGroup, False)
        if len(enemyCollisions) > 0:
            if not self.hitRecently:
                self.handleHit()

        if self.rect.top > SCREEN_HEIGHT:
            self.health = 0

        if self.hitRecently < 0:
            self.hitRecently = False
        else:
            self.hitRecently-=sTime

        if not onGround:
            if self.vector[1] > self.speed*3.0:
                self.vector[1] = self.speed*3.0
            else:
                self.vector[1]+=10

        if self.vector[0] > 0:
            if not blockedRight:
                if not onGround:
                    self.image = self.fallingRight[self.fallAnimation]
                else:
                    self.image = self.runningRight[self.runAnimation]
                self.position+=self.vector * sTime
                self.updateRect()
                self.standing = self.standRight
        elif self.vector[0] < 0:
            if not blockedLeft:
                if not onGround:
                    self.image = self.fallingLeft[self.fallAnimation]
                else:
                    self.image = self.runningLeft[self.runAnimation]
                self.position+=self.vector * sTime
                self.updateRect()
                self.standing = self.standLeft
        elif not onGround:
            if self.standing == self.standRight:
                self.image = self.fallingRight[self.fallAnimation]
            if self.standing == self.standLeft:
                self.image = self.fallingLeft[self.fallAnimation]
            self.position+=self.vector * sTime
            self.updateRect()
        else:
            self.image = self.standing

        if not self.moving:
            if self.time >= .15:
                self.vector[0] = 0
            else:
                if self.vector[0] > 0:
                    self.vector-=10
                if self.vector[0] < 0:
                    self.vector+=10

        if self.time >= .15:
            self.time = 0.0
            if self.runAnimation == 0:
                if self.direction == -1:
                    self.direction = 1
                self.runAnimation+=self.direction
            elif self.runAnimation == 1:
                self.runAnimation+=self.direction
            elif self.runAnimation == 2:
                self.direction = -1
                self.runAnimation+=self.direction

            if self.fallAnimation == 0:
                self.fallAnimation = 1
            elif self.fallAnimation == 1:
                self.fallAnimation = 0

def main():
    pygame.init()
    screen = pygame.display.set_mode(SIZE, 0, 32)
    pygame.font.init()
    gameFont = pygame.font.Font(None, 64)
    if DEBUG:
        debugText = pygame.font.Font(None, 32)
    #
    pygame.display.set_caption("""Meal's Last Keen!""")
    pygame.mouse.set_visible(1)

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))

    windowSheet = SpriteSheet("windowsSheet.png")
    dinnersReady = windowSheet.getSlice((0, 0, 167, 21))
    controlsWindow = windowSheet.getSlice((0, 31, 120, 43))
    endWindow = pygame.transform.scale(windowSheet.getSlice((0, 95, 382, 255)), (SCREEN_WIDTH, SCREEN_HEIGHT))

    level = Map()
    player = Player(level.startLocation, level.enemies)

    clock = pygame.time.Clock()
    while True:
        sTime = clock.tick() / 1000.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == K_d:
                    player.moving = True
                    player.vector[0] = player.speed
                if event.key == K_a:
                    player.moving = True
                    player.vector[0] = -player.speed
                if event.key == K_SPACE:
                    player.jump()
                if event.key == K_ESCAPE:
                    sys.exit()
            if event.type == pygame.KEYUP:
                if event.key == K_d:
                    player.moving = False
                if event.key == K_a:
                    player.moving = False

        screen.blit(background, (0, 0))

        ### Player/Level Updates
        player.update(sTime, level.blocked)
        level.update(sTime)
        gameTimer = gameFont.render(str(int(level.gameTime)), True, (255, 255, 255))
        if player.health <= 0 or level.gameTime <= 0:
            level = Map()
            player = Player(level.startLocation, level.enemies)
        
        if player.rect.right > SCREEN_WIDTH:
            player.position[0] = -16
            level.moveRight = True
        else:
            level.moveRight = False
        if player.rect.left < 0:
            player.position[0] = (SCREEN_WIDTH-player.image.get_width()+32)
            level.moveLeft = True
        else:
            level.moveLeft = False

        screen.blit(level.draw(), level.position)
        level.enemies.draw(screen)
        screen.blit(player.draw(), player.position)
        screen.blit(player.drawHealth(), (0, 0))
        screen.blit(gameTimer, (SCREEN_WIDTH-100,0))
        if level.offset == 0:
            screen.blit(dinnersReady, (60, 260))
            screen.blit(controlsWindow, (60, 400))
        checkEndgame = pygame.sprite.spritecollide(player, level.ending, False)
        if len(checkEndgame) > 0:
            screen.fill((0, 0, 0))
            screen.blit(endWindow, (0,0))

        if DEBUG:
            myFps = debugText.render(str(int(clock.get_fps())), True, (255, 0, 0))
            levelLocation = debugText.render('%s' % (level.offset), True, (255, 0, 0))
            playerPos = debugText.render('%s,%s' % (int(player.position[0]), int(player.position[1])), True, (255, 0, 0))
            screen.blit(playerPos, (player.position[0], player.position[1]-20))
            screen.blit(myFps, (0, 0))
            screen.blit(levelLocation, (0, 20))
            print pygame.mouse.get_pos()
            for sprite in level.triggerGroup:
                pygame.draw.rect(screen, (255, 0, 0), sprite.rect, 1)
            for sprite in player.boundingBoxes:
                pygame.draw.rect(screen, (0, 255, 0), sprite.rect, 1)
            for sprite in level.enemies:
                pygame.draw.rect(screen, (255, 0, 0), sprite.rect, 1)
            playerCollisions = pygame.sprite.spritecollide(player, level.blocked, False)
            if playerCollisions:
                for sprite in playerCollisions:
                    pygame.draw.rect(screen, (0, 0, 255, 20), sprite.rect)

        pygame.display.flip()

if __name__ == "__main__":
    main()
