import pygame
import random

class Fighter:
    def __init__(self,player, x, y,flip, data, sprite_sheet,animation_steps, is_cpu=False):
        self.player = player
        self.size=data[0]
        self.image_scale = data[1]
        self.offset = data[2]
        self.flip = flip
        self.animation_list = self.load_images(sprite_sheet, animation_steps)
        self.action = 0
        self.frame_index = 0
        self.image = self.animation_list[self.action][self.frame_index]
        self.update_time = pygame.time.get_ticks()
        self.rect=pygame.Rect((x, y, 80, 180))
        self.vel_y=0
        self.running = False
        self.jump=False
        self.attacking= False
        self.attack_type=0
        self.attack_cooldown = 0
        self.hit = False
        self.health=100
        self.alive = True
        self.is_cpu=is_cpu

    def load_images(self, sprite_sheet, animation_steps):
        # extract images from spritesheet
        animation_list = []
        for y, animation in enumerate(animation_steps):
            temp_img_list = []
            for x in range(animation):
                temp_img =sprite_sheet.subsurface(x*self.size, y*self.size, self.size, self.size)
                temp_img_list.append(
                    pygame.transform.scale(temp_img,(self.size*self.image_scale, self.size*self.image_scale)))
            animation_list.append(temp_img_list)
        return animation_list

    def move(self, screen_width, screen_height, target, round_over):
        SPEED = 10
        GRAVITY = 2
        dx = 0
        dy = 0
        self.running=False
        self.attack_type = 0

        key = pygame.key.get_pressed()

        if self.attacking == False and self.alive == True and round_over == False:
            if self.player == 1:
                if key[pygame.K_a]:
                    dx = -SPEED
                    self.running = True
                if key[pygame.K_d]:
                    dx = SPEED
                    self.running=True
                if key[pygame.K_w] and self.jump==False:
                    self.vel_y = -30
                    self.jump = True
                if key[pygame.K_r] or key[pygame.K_t]:
                    self.attack(target)
                    if key[pygame.K_r]:
                        self.attack_type=1
                    if key[pygame.K_t]:
                        self.attack_type=2
            elif self.player==2:
                if not hasattr(self, 'cpu_state'):
                    self.cpu_state="idle"
                    self.cpu_think_time = pygame.time.get_ticks()
                    self.cpu_direction=0
                now = pygame.time.get_ticks()
                if now - self.cpu_think_time > random.randint(500, 1000):
                    distance = abs(target.rect.centerx-self.rect.centerx)
                    if distance > 250:
                        self.cpu_state = "approach"
                    elif 120 < distance <= 250:
                        self.cpu_state = random.choice(["idle", "approach", "retreat"])
                    else:
                        self.cpu_state="attack"
                    self.cpu_direction=random.choice([-1, 0, 1])
                    self.cpu_think_time = now
                # Perform action based on state
                if self.cpu_state == "approach":
                    if target.rect.centerx < self.rect.centerx:
                        dx=-SPEED
                    else:
                        dx=SPEED
                    self.running=True
                elif self.cpu_state == "retreat":
                    if target.rect.centerx < self.rect.centerx:
                        dx = SPEED
                    else:
                        dx = -SPEED
                    self.running = True
                elif self.cpu_state == "idle":
                    dx = self.cpu_direction * SPEED
                    self.running = bool(self.cpu_direction)
                elif self.cpu_state == "attack":
                    if self.attack_cooldown == 0:
                        self.attack(target)
                        self.attack_type = 1

        self.vel_y += GRAVITY
        dy += self.vel_y

        # game stays on screen
        if self.rect.left+dx < 0:
            dx = -self.rect.left
        if self.rect.right+dx > screen_width:
            dx = screen_width - self.rect.right
        if self.rect.bottom + dy > screen_height - 110:
            self.vel_y=0
            self.jump=False
            dy = screen_height-110-self.rect.bottom

        # cpu face player
        if target.rect.centerx > self.rect.centerx:
            self.flip = False
        else:
            self.flip = True

        # attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # update player position (for behavior model)
        self.rect.x += dx
        self.rect.y += dy

    def update(self):
        # check what action the player is performing
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.update_action(6)  # 6: death
        elif self.hit:
            self.update_action(5)  # 5: hit
        elif self.attacking:
            if self.attack_type == 1:
                self.update_action(3)  # 3: attack1
            elif self.attack_type == 2:
                self.update_action(4)  # 4: attack2
        elif self.jump:
            self.update_action(2)  # 2: jump
        elif self.running:
            self.update_action(1)  # 1: run
        else:
            self.update_action(0)  # 0: idle

        animation_cooldown = 50
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.frame_index += 1
            self.update_time=pygame.time.get_ticks()
        if self.frame_index >= len(self.animation_list[self.action]):
            if not self.alive:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0
                if self.action == 3 or self.action == 4:
                    self.attacking = False
                    self.attack_cooldown = 20
                if self.action==5:
                    self.hit = False
                    self.attacking = False
                    self.attack_cooldown=20

    def attack(self, target):
        if self.attack_cooldown==0:
            self.attacking = True
            attacking_rect = pygame.Rect(self.rect.centerx-(2 * self.rect.width * self.flip), 
                                         self.rect.y, 2 * self.rect.width, self.rect.height)
            if attacking_rect.colliderect(target.rect):
                damage = 10
                if self.is_cpu:
                    # nerfs cpu
                    damage = int(damage*0.85)  # CPU does 15% less damage because it is learning and will beat you otherwise
                target.health -= damage
                target.hit = True

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time=pygame.time.get_ticks()

    def draw(self, surface):
        img = pygame.transform.flip(self.image, self.flip, False)
        surface.blit(img,(self.rect.x -(self.offset[0]*self.image_scale), 
                           self.rect.y-(self.offset[1]*self.image_scale)))
