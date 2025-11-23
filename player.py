import pygame
from settings   import *
from support    import import_folder
from weapon     import Weapon
from entity     import Entity
from random     import randint

class Player(Entity):
    def __init__(self,  pos,  groups,  obstacle_sprites, create_attack, destroy_attack, create_magic, player_data):
        """
        Player class
        
        Args:
        pos (tuple): position of the player
        groups (pygame.sprite.Group): sprite group
        obstacle_sprites (pygame.sprite.Group): sprite group
        create_attack (function): function to create an attack
        destroy_attack (function): function to destroy an attack
        create_magic (function): function to create a magic
        player_data (list): player data

        Attributes:
        image (pygame.Surface): player image
        rect (pygame.Rect): player rect
        hitbox (pygame.Rect): player hitbox
        player_data (list): player data
        animations (dict): player animations
        status (str): player status
        attacking (bool): player attacking
        attack_cooldown (int): player attack cooldown
        attack_time (int): player attack time
        obstacle_sprites (pygame.sprite.Group): sprite group
        death_sound (pygame.mixer.Sound): death sound

        Methods:
        import_player_assets: import player assets from graphics folder
        get_random_position: get a random position on the map

        """
        super().__init__(groups)
        self.image      = pygame.image.load('./graphics/skin/2/down/down_0.png').convert_alpha()
        self.rect       = self.image.get_rect(topleft = pos)
        self.hitbox     = self.rect.inflate(-6, HITBOX_OFFSET['player'])
        self.player_data= player_data

        #graphics setup
        self.import_player_assets()
        self.status = 'down'

        #movement
        self.attacking       = False
        self.attack_cooldown = 400
        self.attack_time     = None
        self.obstacle_sprites= obstacle_sprites
        self.death_sound     = pygame.mixer.Sound('./audio/death.wav')

        #weapon
        self.create_attack              = create_attack
        self.destroy_attack             = destroy_attack
        self.weapon_index               = 0
        self.weapon                     = list(weapon_data.keys())[self.weapon_index]
        self.can_switch_weapon          = True
        self.weapon_switch_time         = None
        self.switch_duration_cooldown   = 200

        #magic
        self.magic_index        = 0
        self.magic              = list(magic_data.keys())[self.magic_index]
        self.can_switch_magic   = True
        self.magic_switch_time  = None
        self.create_magic       = create_magic

        #stats
        self.stats          = {'health': 100, 'energy': 60 , 'attack': 10 , 'magic': 4  , 'speed': 5}
        self.max_stats      = {'health': 300, 'energy': 140, 'attack': 20 , 'magic': 10 , 'speed': 10}
        self.upgrade_cost   = {'health': 100, 'energy': 100, 'attack': 100, 'magic': 100, 'speed': 100}
        self.health = eval(self.player_data[2][1])
        self.energy = eval(self.player_data[3][1])
        self.exp    = eval(self.player_data[1][1])
        self.speed  = eval(self.player_data[5][1])

        #damage timer
        self.vulnerable = True
        self.hurt_time  = None
        self.invulnerability_duration = 500

        #import a sound
        self.weapon_attack_sound = pygame.mixer.Sound('./audio/sword.wav')
        self.weapon_attack_sound.set_volume(0.4)

    def import_player_assets(self):
        """
        Import player assets from graphics folder
        """
        
        character_path = f'./graphics/skin/{self.player_data[0][1]}/'
        self.animations = { 'up':[], 'down':[], 'left':[], 'right':[],
                           'up_idle':[], 'down_idle':[], 'left_idle':[], 'right_idle':[],
                           'up_attack':[], 'down_attack':[], 'left_attack':[], 'right_attack':[]}

        for animation in self.animations.keys():
            full_path = character_path + animation
            self.animations[animation] = import_folder(full_path)

    def get_random_position(self):
        """
        Get a random position on the map
        """
        x = randint(64, WIDTH-128)
        y = randint(64, HEIGHT-128)
        return x, y

    def input(self):
        """
        Handle player input
        """
        if not self.attacking:
            keys = pygame.key.get_pressed()

            #movement input
            if keys[pygame.K_UP]:
                self.direction.y = -1
                self.status = 'up'
            elif keys[pygame.K_DOWN]:
                self.direction.y = 1
                self.status = 'down'
            else:
                self.direction.y = 0

            if keys[pygame.K_LEFT]:
                self.direction.x = -1
                self.status = 'left'
            elif keys[pygame.K_RIGHT]:
                self.direction.x = 1
                self.status = 'right'
            else:
                self.direction.x = 0

            # attack input
            if keys[pygame.K_SPACE]:
                self.attacking = True
                self.attack_time = pygame.time.get_ticks()
                self.create_attack()
                self.weapon_attack_sound.play()

            # magic input
            if keys[pygame.K_LCTRL]:
                self.attacking = True
                self.attack_time = pygame.time.get_ticks()
                style = list(magic_data.keys())[self.magic_index]
                strength = list(magic_data.values())[self.magic_index]['strength']+ self.stats['magic']
                cost = list(magic_data.values())[self.magic_index]['cost']
                self.create_magic(style, strength, cost)
                if self.magic_index == 2:
                    random_pos = self.get_random_position()
                    self.change_pos(random_pos)

            # switch weapon 
            if keys[pygame.K_q] and self.can_switch_weapon:
                self.can_switch_weapon = False
                self.weapon_switch_time = pygame.time.get_ticks()
                if self.weapon_index < len(list(weapon_data.keys()))-1:
                    self.weapon_index += 1
                else:
                    self.weapon_index = 0 
                self.weapon =list(weapon_data.keys())[self.weapon_index]

            # switch magic  
            if keys[pygame.K_e] and self.can_switch_magic:
                self.can_switch_magic = False
                self.magic_switch_time = pygame.time.get_ticks()

                if self.magic_index < len(list(magic_data.keys()))-1:
                    self.magic_index += 1
                else:
                    self.magic_index = 0 
                self.magic =list(magic_data.keys())[self.magic_index]


    def get_status(self):
        #idel status
        if self.direction.x ==0 and self.direction.y ==0:
            if not 'idle' in self.status and not 'attack' in self.status:
                self.status = self.status + '_idle'

        if self.attacking:
            self.direction.x =0
            self.direction.y =0
            if not 'attack' in self.status:
                if 'idle' in self.status:
                    self.status = self.status.replace('_idle', '_attack')
                else:
                    self.status = self.status + '_attack'
        else:
            if 'attack' in self.status:
                self.status = self.status.replace('_attack', '')

    def cooldowns(self):
        current_time = pygame.time.get_ticks()  
        if self.attacking:
            if current_time - self.attack_time >= self.attack_cooldown+ weapon_data[self.weapon]['cooldown']:
                self.attacking = False
                self.destroy_attack()

        if not self.can_switch_weapon:
            if current_time - self.weapon_switch_time >= self.switch_duration_cooldown:
                self.can_switch_weapon = True
        if not self.can_switch_magic:
            if current_time - self.magic_switch_time >= self.switch_duration_cooldown:
                self.can_switch_magic = True
        if not self.vulnerable:
            if current_time - self.hurt_time >= self.invulnerability_duration:
                self.vulnerable = True

    def animate(self):
        animation = self.animations[self.status]

        #loop over the fram index
        self.frame_index += self.animation_speed
        if self.frame_index >= len(animation):
            self.frame_index =0

        #set the image
        self.image = animation[int(self.frame_index)]
        self.rect = self.image.get_rect(center = self.hitbox.center)

        #flicker
        if not self.vulnerable:
            alpha = self.wave_value()
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)

    def energy_recovery(self):
        if self.energy < self.stats['energy']:
            self.energy += 0.01 * self.stats['magic']
        else:
            self.energy = self.stats['energy']

    def get_full_weapon_damage(self):
        base_damage = self.stats['attack']
        weapon_damage = weapon_data[self.weapon]['damage']
        return base_damage + weapon_damage

    def is_dead(self):
        if self.health <= 0:
            self.kill()
            return self.health<=0

    def get_full_magic_damage(self):
        base_damage = self.stats['magic']
        spell_damage = magic_data[self.magic]['strength']
        return base_damage + spell_damage

    def get_value_by_index(self, index):
        return list(self.stats.values())[index]

    def change_pos(self, new_pos):
        self.rect.topleft = new_pos
        self.hitbox = self.rect.inflate(-6, HITBOX_OFFSET['player'])

    def get_cost_by_index(self, index):
        return list(self.upgrade_cost.values())[index]

    def update(self):
        self.input()
        self.cooldowns()
        self.is_dead()
        self.get_status()
        self.animate()
        self.import_player_assets()
        self.move(self.stats['speed'])
        self.energy_recovery()


class AutoPlayer(Player):
    """
    Player variant that moves automatically between patrol points and triggers
    melee attacks on a fixed cadence. Helpful for AI companions or demo reels.
    """

    def __init__(
        self,
        pos,
        groups,
        obstacle_sprites,
        create_attack,
        destroy_attack,
        create_magic,
        player_data,
        patrol_points=None,
        attack_interval=2000,
        patrol_tolerance=4,
        auto_attack=True,
    ):
        """
        Args:
            patrol_points (list[tuple[int, int]] | None): optional patrol path.
                Defaults to staying at the spawn point.
            attack_interval (int): milliseconds between auto-attacks.
            patrol_tolerance (int | float): radius in pixels considered "at waypoint".
            auto_attack (bool): disable to run patrol-only demonstrations.
        """
        super().__init__(
            pos,
            groups,
            obstacle_sprites,
            create_attack,
            destroy_attack,
            create_magic,
            player_data,
        )
        self.patrol_points = patrol_points or [self.rect.center]
        self._patrol_index = 0
        self.attack_interval = attack_interval
        self._last_attack_ts = pygame.time.get_ticks()
        self.patrol_tolerance = patrol_tolerance
        self.auto_attack = auto_attack

    def input(self):
        """Drive the player toward the next patrol point and auto-attack."""
        if not self.patrol_points:
            self.direction.update(0, 0)
            return

        target = pygame.math.Vector2(self.patrol_points[self._patrol_index])
        current = pygame.math.Vector2(self.rect.center)
        delta = target - current

        if delta.length() <= self.patrol_tolerance:
            # Advance to the next waypoint once close enough.
            self._patrol_index = (self._patrol_index + 1) % len(self.patrol_points)
            self.direction.update(0, 0)
        else:
            move_direction = delta.normalize()
            self.direction.update(move_direction.x, move_direction.y)
            if abs(self.direction.x) > abs(self.direction.y):
                self.status = 'right' if self.direction.x > 0 else 'left'
            else:
                self.status = 'down' if self.direction.y > 0 else 'up'

        if not self.auto_attack:
            return

        now = pygame.time.get_ticks()
        if not self.attacking and now - self._last_attack_ts >= self.attack_interval:
            self.attacking = True
            self.attack_time = now
            self.create_attack()
            self.weapon_attack_sound.play()
            self._last_attack_ts = now
