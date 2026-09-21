import random, arcade

from pyglet.event import EVENT_HANDLE_STATE


class Agent:
    def __init__(self, x, y, color, attack_range = 150, offset = 0):
        self.Q = {}
        for dx in range(-9, 10):
            for dy in range(-2, 3):
                for a in range(0, 3):
                    for b in range(0, 2):
                        self.Q[(dx, dy, a, b)] = [0.0] * 10
        self.x = x
        self.y = y
        self.hp = 100
        self.attack_cooldown = 10
        self.color = color
        self.rect = arcade.rect.LBWH(self.x - 10, self.y - 30, 20, 60)
        self.direction = 1
        self.offset = offset
        self.attack_range = attack_range
        self.attack_hitbox = arcade.rect.LBWH(self.x + self.offset * self.direction, self.y - 30, self.attack_range * self.direction, 60)
        self.jump = False
        self.hitbox = True
        self.a = 0
        self.jump_strength = 20
        self.V = 7
        self.epsilon = 1.0
        self.gamma = 0.95
        self.last_reward = 0
        self.snipe = (0, 0, 0, 0)
        self.actions = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.miss = False
        self.dead = False


    def draw(self):
        arcade.draw_rect_filled(self.rect, self.color, 0)
        if self.hitbox:
            arcade.draw_rect_outline(self.attack_hitbox, self.color, 1, 0)
        snipe_color = [0, 0, 0]
        snipe_color[self.color.index(max(self.color))] = max(0, min(250, self.attack_cooldown * 20))
        if self.snipe != (0, 0, 0, 0): arcade.draw_line(self.snipe[0], self.snipe[1], self.snipe[2], self.snipe[3], tuple(snipe_color), 2)



    def attack(self, who, snipe=False):
        start_hp = who.hp
        if (self.attack_hitbox.overlaps(who.rect) and self.attack_cooldown < 0) or ((abs(self.y - who.y) < 30 and snipe and (self.x - who.x) * self.direction * -1 > 0 and self.attack_cooldown < 0)):
            who.hp -= 5
            if snipe:
                who.hp -= 10
        if snipe:
            if  self.attack_cooldown < 0:
                self.snipe = (self.x, self.y, 1010 * self.direction, self.y)
            self.attack_cooldown = 25
        else: self.attack_cooldown = 10
        if who.hp >= start_hp or self.attack_cooldown >= 0:
            self.miss = True


    def act(self, other):
        state = round(self.x/100 + 0.5) - round(other.x/100 + 0.5), round(self.y/100 + 0.5) - round(other.y/100 + 0.5), 1 if self.attack_hitbox.overlaps(other.rect) and self.attack_cooldown < 0 else (2 if not self.attack_hitbox.overlaps(other.rect) and self.attack_cooldown < 0 else 0), 1 if self.direction == 1 else 0
        st1 = state
        sthp = other.hp
        best = max(self.Q[state])

        best_pool = [a for a in range(10) if self.Q[state][a] == best]

        action = random.choice(best_pool)
        if random.random() < self.epsilon:
            action = random.randrange(0, 10)

        if action == 0:
            self.direction = -1
            self.x -= self.V
        elif action == 1:
            self.direction = 1
            self.x += self.V
        elif action == 2:
            pass
        elif action == 3:
            self.jump = True
        elif action == 4:
            self.direction = -1
            self.x -= self.V
            self.jump = True
        elif action == 5:
            self.direction = 1
            self.x += self.V
            self.jump = True
        elif action == 6:
            self.attack(other)
        elif action == 7:
            self.direction = -1
            self.x -= self.V
            self.attack(other)
        elif action == 8:
            self.direction = 1
            self.x += self.V
            self.attack(other)
        elif action == 9:
            self.attack(other, True)

        self.actions[action] += 1

        self.x = min(990, max(10, self.x))
        self.y = max(60, self.y)

        st2 = round(self.x/100 + 0.5) - round(other.x/100 + 0.5), round(self.y/100 + 0.5) - round(other.y/100 + 0.5), 1 if self.attack_hitbox.overlaps(other.rect) and self.attack_cooldown < 0 else (2 if not self.attack_hitbox.overlaps(other.rect) and self.attack_cooldown < 0 else 0), 1 if self.direction == 1 else 0

        if len(self.Q[st2]) != 11: self.Q[st2].append(0.0)

        if other.hp < sthp:
            self.reward(0.01, st1, action, st2)
            if other.hp <= 0: self.reward(0.02, st1, action, st2)
        else: self.reward(-0.002, st1, action, st2)
        if abs(self.x - other.x) < 70: self.reward(-0.5, st1, action, st2)
        elif abs(self.x - other.x) > 400: self.reward(-0.004, st1, action, st2)
        if self.miss:
            self.reward(-0.3, st1, action, st2)
            self.miss = False


        self.epsilon = max(0.05, self.epsilon * 0.9995)

    def update(self):
        self.rect = arcade.rect.LBWH(self.x - 10, self.y - 30, 20, 60)
        self.attack_hitbox = arcade.rect.LBWH(self.x + self.offset * self.direction, self.y - 30, self.attack_range * self.direction, 60)
        self.attack_cooldown -= 1

        if self.jump:

            if self.a <= 0 and self.y <= 60: self.a = self.jump_strength

            self.y += self.a
            self.a -= 1
            if self.y <= 60:
                self.a = 0
                self.jump = False
        if self.attack_cooldown < 0:
            self.snipe = (0, 0, 0, 0)

    def reward(self, reward, state2, act, state):
        value = self.Q[state][act]
        next_value = max(self.Q[state2])
        rew = 0.05 + (reward + self.gamma * next_value - 0.2) * 0.1
        self.Q[state][act] = rew
        self.last_reward = rew


class Player():
    def __init__(self, x, y, color, attack_range=150, offset=0):
        self.x = x
        self.y = y
        self.hp = 100
        self.attack_cooldown = 10
        self.color = color
        self.rect = arcade.rect.LBWH(self.x - 10, self.y - 30, 20, 60)
        self.direction = 1
        self.offset = offset
        self.attack_range = attack_range
        self.attack_hitbox = arcade.rect.LBWH(self.x + self.offset * self.direction, self.y - 30, self.attack_range * self.direction, 60)
        self.jump = False
        self.hitbox = True
        self.a = 0
        self.jump_strength = 20
        self.V = 7
        self.snipe = (0, 0, 0, 0)
        self.dead = False

    def draw(self):
        arcade.draw_rect_filled(self.rect, self.color, 0)
        if self.hitbox:
            arcade.draw_rect_outline(self.attack_hitbox, self.color, 1, 0)
        snipe_color = max(0, min(250, self.attack_cooldown * 20))
        if self.snipe != (0, 0, 0, 0): arcade.draw_line(self.snipe[0], self.snipe[1], self.snipe[2], self.snipe[3], (snipe_color, snipe_color, snipe_color), 2)

    def attack(self, who, snipe=False):
        start_hp = who.hp
        if (self.attack_hitbox.overlaps(who.rect) and self.attack_cooldown < 0) or (abs(self.y - who.y) < 30 and snipe and (self.x - who.x) * self.direction * -1 > 0 and self.attack_cooldown < 0):
            who.hp -= 5
            if snipe:
                who.hp -= 10
        if snipe:
            if  self.attack_cooldown < 0:
                self.snipe = (self.x, self.y, 1010 * self.direction, self.y)
            self.attack_cooldown = 25
        else: self.attack_cooldown = 10

    def update(self, held_keys, enemy):
        self.rect = arcade.rect.LBWH(self.x - 10, self.y - 30, 20, 60)
        self.attack_hitbox = arcade.rect.LBWH(self.x + self.offset * self.direction, self.y - 30, self.attack_range * self.direction, 60)
        self.attack_cooldown -= 1

        if arcade.key.A in held_keys:
            self.x -= self.V
            self.direction = -1
        if arcade.key.D in held_keys:
            self.x += self.V
            self.direction = 1
        if arcade.key.W in held_keys or arcade.key.SPACE in held_keys:
            self.jump = True
        if arcade.key.L in held_keys:
            self.attack(enemy)
        if arcade.key.K in held_keys:
            self.attack(enemy, True)


        if self.jump:
            if self.a <= 0 and self.y <= 60: self.a = self.jump_strength

            self.y += self.a
            self.a -= 1
            if self.y <= 60:
                self.a = 0
                self.jump = False
        if self.attack_cooldown < 0:
            self.snipe = (0, 0, 0, 0)


        self.x = min(990, max(10, self.x))
        self.y = max(60, self.y)


def save(file, dict):
    f = open(file, 'wt')
    f.write(str(dict))
    f.close()


def floor(a, b = 0):
    return round(a-0.5, b)


run = True
am_pl = 2
to1v1 = False
against = ''
use_save = False

class Menu(arcade.Window):
    def __init__(self, W, H, title):
        super().__init__(W, H, title)
        arcade.set_background_color(arcade.color.BLACK)
        self.frame = 0
        self.W = W
        self.H = H

        self.players = arcade.rect.LBWH(50, H/2 - 35, 100, 70)
        self.am_pl = 2

        self.to1v1_fight = arcade.rect.LBWH(W - 120, H/2 - 35, 100, 70)
        self.to1v1 = False

        self.start = arcade.rect.LBWH(W/2 - 75, H/2 - 35, 150, 70)
        self.exit = arcade.rect.LBWH(W/2 - 30, H/2 - 120, 60, 40)

        self.against_red = arcade.rect.LBWH(W/2 - 140, H - 150, 80, 50)
        self.against_blue = arcade.rect.LBWH(W/2 - 40, H - 150, 80, 50)
        self.against_green = arcade.rect.LBWH(W/2 + 60, H - 150, 80, 50)

        self.use_saves = arcade.rect.LBWH(W / 2 - 45, 20, 90, 40)

    def on_draw(self):
        global use_save
        self.clear()

        arcade.draw_rect_filled(self.players, (200, 100, 100) if self.am_pl == 2 else (100, 200, 100))
        arcade.draw_text(self.am_pl, self.players.lbwh[0] + self.players.lbwh[2] / 2, self.players.lbwh[1] + self.players.lbwh[3] / 2, (200, 200, 200), self.players.lbwh[3] - 20, anchor_x='center', anchor_y='center')

        arcade.draw_rect_filled(self.to1v1_fight, (200, 100, 100) if not self.to1v1 else (100, 200, 100))
        arcade.draw_text('To a 1v1', self.to1v1_fight.lbwh[0] + self.to1v1_fight.lbwh[2] / 2, self.to1v1_fight.lbwh[1] + self.to1v1_fight.lbwh[3] / 2, (200, 200, 200), self.to1v1_fight.lbwh[3] - 50, anchor_x='center', anchor_y='center')

        arcade.draw_rect_filled(self.start, (120, 120, 120))
        arcade.draw_text('Start', self.start.lbwh[0] + 10, self.start.lbwh[1] + self.start.lbwh[3] / 2, (200, 200, 200), self.start.lbwh[3] - 20, anchor_y='center')
        arcade.draw_rect_filled(self.exit, (120, 120, 120))
        arcade.draw_text('Exit', self.exit.lbwh[0] + 10, self.exit.lbwh[1] + self.exit.lbwh[3] / 2, (200, 200, 200), self.exit.lbwh[3] - 20, anchor_y='center')

        arcade.draw_rect_filled(self.against_red, (200, 120, 120))
        arcade.draw_rect_filled(self.against_blue, (120, 120, 200))
        arcade.draw_rect_filled(self.against_green, (120, 200, 120))

        arcade.draw_rect_filled(self.use_saves, (200, 150, 150) if not use_save else (150, 200, 150))
        arcade.draw_text('Saves', self.use_saves.lbwh[0] + self.use_saves.lbwh[2] / 2, self.use_saves.lbwh[1] + self.use_saves.lbwh[3] / 2, (200, 200, 200), 25, anchor_y='center', anchor_x='center')

    def check_mouse(self, lbwh, x, y):
        if lbwh.lbwh[0] < x and lbwh.lbwh[0] + lbwh.lbwh[2] > x and lbwh.lbwh[1] < y and lbwh.lbwh[1] + lbwh.lbwh[3] > y:
            return True
        else: return False


    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        global run, am_pl, to1v1, against, use_save
        am_pl = self.am_pl
        to1v1 = self.to1v1
        if self.check_mouse(self.players, x, y):
            self.am_pl = 3 if self.am_pl == 2 else 2
        elif self.check_mouse(self.to1v1_fight, x, y):
            self.to1v1 = not self.to1v1
        elif self.check_mouse(self.start, x, y):
            arcade.close_window()
        elif self.check_mouse(self.exit, x, y):
            run = False
        elif self.check_mouse(self.use_saves, x, y):
            use_save = not use_save

        elif self.check_mouse(self.against_red, x, y):
            against = 'red'
        elif self.check_mouse(self.against_blue, x, y):
            against = 'blue'
        elif self.check_mouse(self.against_green, x, y):
            against = 'green'


    def on_update(self, delta_time: float):
        global run, am_pl, to1v1
        am_pl = self.am_pl
        to1v1 = self.to1v1
        if not run: arcade.close_window()




agent1 = Agent(250, 60, (200, 30, 30))
agent2 = Agent(750, 60, (30, 30, 200))
agent3 = Agent(500, 60, (30, 200, 30))

player = Player(500, 60, (230, 230, 230))




class Window(arcade.Window):
    def __init__(self, W, H, title):
        global am_pl, to1v1, against
        super().__init__(W, H, title)
        arcade.set_background_color(arcade.color.BLACK)
        self.frame = 0
        self.episode = 1
        self.red = 0
        self.blue = 0
        self.green = 0
        self.am_pl = am_pl
        self.to1v1 = to1v1
        self.against = against
        self.grid = False
        self.fps = 60
        self.avg_episode_time = 0
        self.camera = arcade.camera.Camera2D()
        self.dead = 0

        self.held_keys = []


        if use_save:
            try:
                with open('saved/ag1.txt', 'r') as file:
                    ag1 = file.read()
                agent1.Q = eval(ag1)
                agent1.epsilon = 0.05
            except FileNotFoundError:
                pass

            try:
                with open('saved/ag2.txt', 'r') as file:
                    ag2 = file.read()
                agent2.Q = eval(ag2)
                agent2.epsilon = 0.05
            except FileNotFoundError:
                pass

            if am_pl == 3:
                try:
                    with open('saved/ag3.txt', 'r') as file:
                        ag3 = file.read()
                    agent3.Q = eval(ag3)
                    if am_pl == 3:
                        agent3.epsilon = 0.05
                except FileNotFoundError:
                    pass



        save('ag1.txt', agent1.Q)
        save('ag2.txt', agent2.Q)
        if am_pl == 3:
            save('ag3.txt', agent3.Q)

    def on_draw(self):
        self.clear()
        self.camera.use()

        if self.grid:
            for x in range(0, 1001, 100):
                for y in range(0, 601, 100):
                    arcade.draw_line(x, y-600, x, y+600, (50, 50, 50), 1)
                    arcade.draw_line(x-1000, y, x+1000, y, (50, 50, 50), 1)
            arcade.draw_lbwh_rectangle_outline(floor(agent1.x/100)*100, floor(agent1.y/100)*100, 100, 100, (100, 100, 100), 1)
            arcade.draw_lbwh_rectangle_outline(floor(agent2.x/100)*100, floor(agent2.y/100)*100, 100, 100, (100, 100, 100), 1)
            if self.am_pl == 3:
                arcade.draw_lbwh_rectangle_outline(floor(agent3.x/100)*100, floor(agent3.y/100)*100, 100, 100, (100, 100, 100), 1)

        if self.against == '':
            agent1.draw()
            agent2.draw()
            if self.am_pl == 3:
                agent3.draw()
        if self.against == 'red': agent1.draw()
        elif self.against == 'blue': agent2.draw()
        else: agent3.draw()
        if self.against != '':
            player.draw()


        arcade.draw_line(-10, 30, 1010, 30, (255, 255, 255), 2)

        if self.against != 'blue' and self.against != 'green':
            arcade.draw_text(agent1.hp, 20, 480, (220, 50, 50), 24)
            arcade.draw_text(f'Last reward: {round(agent1.last_reward, 2)}', 20, 510, (220, 50, 50), 24)
            arcade.draw_text(f'Cooldown: {agent1.attack_cooldown}', 20, 540, (220, 50, 50), 24)
            arcade.draw_text(f'epsilon: {round(agent1.epsilon, 3)}', 20, 570, (220, 50, 50), 24)

            maxam1 = max(agent1.actions)
            for i, am in enumerate(agent1.actions):
                arcade.draw_lbwh_rectangle_filled(i*30 + 10, 350, 20, am/maxam1 * 100, (230, 230, 230))


        if self.against != 'red' and self.against != 'green':
            arcade.draw_text(agent2.hp, 1000-20, 480, (50, 50, 220), 24, anchor_x='right')
            arcade.draw_text(f'Last reward: {round(agent2.last_reward, 2)}', 1000-20, 510, (50, 50, 220), 24, anchor_x='right')
            arcade.draw_text(f'Cooldown: {agent2.attack_cooldown}', 1000-20, 540, (50, 50, 220), 24, anchor_x='right')
            arcade.draw_text(f'epsilon: {round(agent2.epsilon, 3)}', 1000-20, 570, (50, 50, 220), 24, anchor_x='right')

            maxam2 = max(agent2.actions)
            for i, am in enumerate(agent2.actions):
                arcade.draw_lbwh_rectangle_filled(i*30 + 1000 - 30 * len(agent2.actions), 350, 20, am/maxam2 * 100, (230, 230, 230))



        if self.am_pl == 3 or self.against == 'green':
            if self.against != 'red' and self.against != 'blue':
                arcade.draw_text(agent3.hp, 500, 480, (50, 220, 50), 24, anchor_x='center')
                arcade.draw_text(f'Last reward: {round(agent3.last_reward, 2)}', 500, 510, (50, 220, 50), 24, anchor_x='center')
                arcade.draw_text(f'Cooldown: {agent3.attack_cooldown}', 500, 540, (50, 220, 50), 24, anchor_x='center')
                arcade.draw_text(f'epsilon: {round(agent3.epsilon, 3)}', 500, 570, (50, 220, 50), 24, anchor_x='center')

                maxam3 = max(agent3.actions)
                for i, am in enumerate(agent3.actions):
                    arcade.draw_lbwh_rectangle_filled(i*30 + 655 - 30 * len(agent3.actions), 350, 20, am/maxam3 * 100, (230, 230, 230))

        if self.against != '':
            arcade.draw_text(player.hp, 500, 50, (230, 230, 230), 16, anchor_y='center', anchor_x='center')
            arcade.draw_text(f'Cooldown: {player.attack_cooldown}', 500, 70, (230, 230, 230), 16, anchor_y='center', anchor_x='center')




        arcade.draw_text(self.episode, 500, 150 if self.am_pl == 3 else 540, (220, 220, 220), 24, anchor_x='center')

        if self.against != 'red' and self.against != 'green':
            arcade.draw_text(self.blue, 540, 120 if self.am_pl == 3 else 510, (50, 50, 220), 24, anchor_x='left')
        if self.am_pl == 3:
            if self.against != 'red' and self.against != 'blue':
                arcade.draw_text(self.green, 500, 120, (50, 220, 50), 24, anchor_x='center')
        if self.against != 'blue' and self.against != 'green':
            arcade.draw_text(self.red, 460, 120 if self.am_pl == 3 else 510, (220, 50, 50), 24, anchor_x='right')

        arcade.draw_text(f'FPS: {round(self.fps, 1)}', 20, 50, (220, 220, 220), 24, anchor_x='left')
        arcade.draw_text(f'Avg length: {round(self.avg_episode_time / 60, 2)} sec', 20, 100, (220, 220, 220), 24, anchor_x='left')

        arcade.draw_text('grid', 950, 50, (220, 220, 220), 24, anchor_x='center')
        arcade.draw_lbwh_rectangle_outline(900, 30, 100, 60, (100, 100, 100), 3)


    def on_update(self, delta_time: float):
        global run

        if not run: arcade.close_window()

        self.frame += 1

        agent1.update()
        agent2.update()
        if self.am_pl == 3 or self.against == 'green':
            agent3.update()
        if self.against != '':
            player.update(self.held_keys, agent1 if self.against == 'red' else (agent2 if self.against == 'blue' else agent3))



        if self.against != '':
            if player.hp <= 0:
                print("Player died", agent1.hp if self.against == 'red' else (agent2.hp if self.againt == 'blue' else agent3.hp))
                player.dead = True
                self.reset()
            if agent1.hp <= 0 or agent2.hp <= 0 or agent3.hp <= 0:
                print("Agent died, humanity wins")
                agent1.dead = True
                agent2.dead = True
                agent3.dead = True
                self.reset()
        if agent1.hp <= 0 and not agent1.dead:
            self.dead += 1
            agent1.dead = True
            if self.against == '': print("RED died", agent2.hp, agent3.hp if self.am_pl == 3 else '')
            self.red += 1
            agent1.y = 2000
            agent1.jump = True
            agent1.color = (*agent1.color, 120)
            if not self.to1v1:
                self.reset()
        if agent2.hp <= 0 and not agent2.dead:
            self.dead += 1
            agent2.dead = True
            if self.against == '': print("BLUE died", agent1.hp, agent3.hp if self.am_pl == 3 else '')
            self.blue += 1
            agent2.y = 2000
            agent2.jump = True
            agent2.color = (*agent2.color, 120)
            if not self.to1v1:
                self.reset()
        if self.am_pl == 3:
            if agent3.hp <= 0 and not agent3.dead:
                self.dead += 1
                agent3.dead = True
                if self.against == '': print("GREEN died", agent1.hp, agent2.hp)
                self.green += 1
                agent3.y = 2000
                agent3.jump = True
                agent3.color = (*agent3.color, 120)
                if not self.to1v1:
                    self.reset()
        if self.am_pl == 3:
            if self.to1v1 and self.dead >= self.am_pl - 1:
                self.reset()

        if self.frame > 36000: self.reset()

        if self.against != '':
            if self.against == 'red' and agent1.hp > 0: agent1.act(player)
            elif self.against == 'blue' and agent2.hp > 0: agent2.act(player)
            elif self.against == 'green' and agent3.hp > 0: agent3.act(player)

        elif self.am_pl == 3:
            if agent3.hp > 0:
                if agent1.hp > 0:
                    agent3.act(agent1)
                if agent2.hp > 0:
                    agent3.act(agent2)

            if agent1.hp > 0:
                if agent2.hp > 0:
                    agent1.act(agent2)
                if agent3.hp > 0:
                    agent1.act(agent3)

            if agent2.hp > 0:
                if agent1.hp > 0:
                    agent2.act(agent1)
                if agent3.hp > 0:
                    agent2.act(agent3)
        else:
            agent2.act(agent1)
            agent1.act(agent2)



        self.fps = 1 / delta_time


    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if x > 900 and y < 100 and y > 30: self.grid = not self.grid

    def on_key_press(self, symbol: int, modifiers: int):
        self.held_keys.append(symbol)
    def on_key_release(self, symbol: int, modifiers: int):
        self.held_keys.remove(symbol)


    def reset(self):
        if self.against == '':
            agent1.x = 250
            agent1.y = 60
            agent1.hp = 100
            agent1.dead = False
            agent1.color = agent1.color[:3]

            agent2.x = 750
            agent2.y = 60
            agent2.hp = 100
            agent2.dead = False
            agent2.color = agent2.color[:3]

            if self.am_pl == 3:
                agent3.x = 750
                agent3.y = 60
                agent3.hp = 100
                agent3.dead = False
                agent3.color = agent3.color[:3]
        else:
            if self.against == 'red':
                agent1.x = 250
                agent1.y = 60
                agent1.hp = 100
                agent1.dead = False
                agent1.color = agent1.color[:3]
            elif self.against == 'blue':
                agent2.x = 750
                agent2.y = 60
                agent2.hp = 100
                agent2.dead = False
                agent2.color = agent2.color[:3]
            elif self.against == 'green':
                agent3.x = 750
                agent3.y = 60
                agent3.hp = 100
                agent3.dead = False
                agent3.color = agent3.color[:3]
            player.x = 500
            player.y = 60
            player.hp = 100
            player.dead = False


        self.avg_episode_time = (self.avg_episode_time * self.episode + self.frame) / (self.episode + 1)
        self.episode += 1
        self.frame = 0
        self.dead = 0

        if self.against != '':
            save('ag1.txt', agent1.Q)
            save('ag2.txt', agent2.Q)
            if self.am_pl == 3:
                save('ag3.txt', agent3.Q)
        elif self.against == 'red':
            save('ag1.txt', agent1.Q)
        elif self.against == 'blue':
            save('ag2.txt', agent2.Q)
        elif self.against == 'green':
            save('ag3.txt', agent3.Q)

menu = Menu(800, 500, 'Menu')
arcade.run()
window = Window(1000, 600, 'RL Agents')
arcade.run()
