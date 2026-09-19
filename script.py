import random, arcade


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


    def draw(self):
        arcade.draw_rect_filled(self.rect, self.color, 0)
        if self.hitbox:
            arcade.draw_rect_outline(self.attack_hitbox, self.color, 1, 0)

        if self.snipe != (0, 0, 0, 0): arcade.draw_line(self.snipe[0], self.snipe[1], self.snipe[2], self.snipe[3], (min(255, max(0, self.attack_cooldown * 20)), min(255, max(0, self.attack_cooldown * 20)), min(255, max(0, self.attack_cooldown * 20))), 2)


    def attack(self, who, snipe = False):
        if (self.attack_hitbox.overlaps(who.rect) or (abs(self.y - who.y) < 60 and snipe and (self.x - who.x) * self.direction * -1 > 0)) and self.attack_cooldown < 0:
            who.hp -= 5
            if snipe:
                who.hp -= 10
                self.snipe = (self.x, self.y, 1010 * self.direction, self.y)
                self.attack_cooldown = 25
            else: self.attack_cooldown = 10
        if snipe: self.attack_cooldown = 25
        else: self.attack_cooldown = 10



    def act(self, other):
        state = round(self.x/100 + 0.5) - round(other.x/100 + 0.5), round(self.y/100 + 0.5) - round(other.y/100 + 0.5), 1 if self.attack_hitbox.overlaps(other.rect) and self.attack_cooldown < 0 else (2 if not self.attack_hitbox.overlaps(other.rect) and self.attack_cooldown < 0 else 0), 1 if self.direction == 1 else 0
        st1 = state
        sthp = other.hp
        #action = self.Q[state].index(max(self.Q[state]))
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


        self.x = min(990, max(10, self.x))
        self.y = min(400, max(60, self.y))

        st2 = round(self.x/100 + 0.5) - round(other.x/100 + 0.5), round(self.y/100 + 0.5) - round(other.y/100 + 0.5), 1 if self.attack_hitbox.overlaps(other.rect) and self.attack_cooldown < 0 else (2 if not self.attack_hitbox.overlaps(other.rect) and self.attack_cooldown < 0 else 0), 1 if self.direction == 1 else 0


        if other.hp < sthp:
            self.reward(0.01, st1, action, st2)
            if other.hp <= 0: self.reward(0.02, st1, action, st2)
        else: self.reward(-0.002, st1, action, st2)
        if abs(self.x - other.x) < 70: self.reward(-10, st1, action, st2)
        elif abs(self.x - other.x) > 600: self.reward(-0.003, st1, action, st2)

        self.epsilon = max(0.05, self.epsilon * 0.9995)

    def update(self):
        self.rect = arcade.rect.LBWH(self.x - 10, self.y - 30, 20, 60)
        self.attack_hitbox = arcade.rect.LBWH(self.x + self.offset * self.direction, self.y - 30, self.attack_range * self.direction, 60)
        self.attack_cooldown -= 1

        if self.jump:

            if self.a <= 0 and self.y <= 60: self.a = self.jump_strength

            self.y += self.a
            self.a -= 1
            if self.y <= 60: self.a = 0
        if self.attack_cooldown < 0:
            self.snipe = (0, 0, 0, 0)

    def reward(self, reward, state2, act, state):
        value = self.Q[state][act]
        next_value = max(self.Q[state2])
        rew = 0.08 + (reward + self.gamma * next_value - 0.2) * 0.1
        self.Q[state][act] = rew
        self.last_reward = rew


agent1 = Agent(250, 60, (200, 30, 30))
agent2 = Agent(750, 60, (30, 30, 200))
print(len(agent1.Q))
def save(file, dict):
    f = open(file, 'wt')
    f.write(str(dict))
    f.close()

save('ag1.json', agent1.Q)
save('ag2.json', agent2.Q)

def floor(a, b = 0):
    return round(a-0.5, b)

class Window(arcade.Window):
    def __init__(self, W, H, title):
        super().__init__(W, H, title)
        arcade.set_background_color(arcade.color.BLACK)
        self.frame = 0
        self.episode = 1
        self.red = 0
        self.blue = 0
        self.grid = True
        self.fps = 60
        self.camera = arcade.camera.Camera2D()

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


        agent1.draw()
        agent2.draw()


        arcade.draw_line(-10, 30, 1010, 30, (255, 255, 255), 2)

        arcade.draw_text(agent1.hp, 20, 480, (220, 50, 50), 24)
        arcade.draw_text(f'Last reward: {round(agent1.last_reward, 2)}', 20, 510, (220, 50, 50), 24)
        arcade.draw_text(f'Cooldown: {agent1.attack_cooldown}', 20, 540, (220, 50, 50), 24)
        arcade.draw_text(f'epsilon: {round(agent1.epsilon, 3)}', 20, 570, (220, 50, 50), 24)

        arcade.draw_text(agent2.hp, 1000-20, 480, (50, 50, 220), 24, anchor_x='right')
        arcade.draw_text(f'Last reward: {round(agent2.last_reward, 2)}', 1000-20, 510, (50, 50, 220), 24, anchor_x='right')
        arcade.draw_text(f'Cooldown: {agent2.attack_cooldown}', 1000-20, 540, (50, 50, 220), 24, anchor_x='right')
        arcade.draw_text(f'epsilon: {round(agent2.epsilon, 3)}', 1000-20, 570, (50, 50, 220), 24, anchor_x='right')


        arcade.draw_text(self.episode, 500, 540, (220, 220, 220), 24, anchor_x='center')
        arcade.draw_text(self.blue, 540, 510, (50, 50, 220), 24, anchor_x='left')
        arcade.draw_text(self.red, 460, 510, (220, 50, 50), 24, anchor_x='right')

        arcade.draw_text(f'FPS: {round(self.fps, 2)}', 20, 50, (220, 220, 220), 24, anchor_x='left')

        arcade.draw_text('grid', 950, 50, (220, 220, 220), 24, anchor_x='center')
        arcade.draw_lbwh_rectangle_outline(900, 30, 100, 60, (100, 100, 100), 3)


    def on_update(self, delta_time: float):
        self.frame += 1

        agent1.update()
        agent2.update()

        if agent1.hp <= 0:
            print("BLUE", agent2.hp)
            self.blue += 1
            self.reset()
        if agent2.hp <= 0:
            print("RED", agent1.hp)
            self.red += 1
            self.reset()

        if self.frame > 36000: self.reset()

        agent1.act(agent2)
        agent2.act(agent1)
        self.fps = 1 / delta_time

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if x > 900 and y < 100 and y > 30: self.grid = not self.grid



    def reset(self):
        agent1.x = 250
        agent1.y = 60
        agent1.hp = 100
        agent2.x = 750
        agent2.y = 60
        agent2.hp = 100
        self.episode += 1
        self.frame = 0

        save('ag1.json', agent1.Q)
        save('ag2.json', agent2.Q)

window = Window(1000, 600, 'RL Agents')
arcade.run()