import random
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty, ListProperty, BooleanProperty, ColorProperty
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line

# --- КОНФИГУРАЦИЯ ---
GRID_SIZE = 8
GAP = dp(2)

# ЦВЕТА (Плоские, яркие, как в первой версии)
COLORS = {
    'bg':         (0.1, 0.1, 0.15, 1),
    'panel':      (0.15, 0.15, 0.22, 1),
    'grid_empty': (0.2, 0.2, 0.25, 1),
    'text':       (0.9, 0.9, 0.9, 1),
    
    # Цвета фигур
    'blue':   (0.2, 0.6, 1.0, 1),
    'green':  (0.2, 0.8, 0.4, 1),
    'red':    (0.9, 0.3, 0.3, 1),
    'yellow': (0.9, 0.8, 0.2, 1),
    'purple': (0.6, 0.3, 0.9, 1),
    'orange': (1.0, 0.5, 0.0, 1),
    'cyan':   (0.2, 0.9, 0.9, 1)
}

SHAPES_DEF = [
    {'coords': [(0, 0)], 'color': 'blue'},
    {'coords': [(0, 0), (1, 0)], 'color': 'green'},
    {'coords': [(0, 0), (0, 1)], 'color': 'green'},
    {'coords': [(0, 0), (1, 0), (2, 0)], 'color': 'red'},
    {'coords': [(0, 0), (0, 1), (0, 2)], 'color': 'red'},
    {'coords': [(0, 0), (1, 0), (0, 1), (1, 1)], 'color': 'yellow'},
    {'coords': [(0, 0), (1, 0), (2, 0), (2, 1)], 'color': 'orange'},
    {'coords': [(0, 0), (1, 0), (2, 0), (0, 1)], 'color': 'orange'},
    {'coords': [(0, 0), (1, 0), (1, 1)], 'color': 'purple'},
    {'coords': [(0, 0), (1, 0), (2, 0), (1, 1)], 'color': 'cyan'},
]

# --- KV STYLES (Минимализм) ---
KV = """
#:import hex kivy.utils.get_color_from_hex

<GameCell>:
    canvas:
        Color:
            rgba: self.display_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(3)]

<GameBoard>:
    canvas.before:
        Color:
            rgba: 0.15, 0.15, 0.22, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(5)]

<SimpleButton@Button>:
    background_normal: ''
    background_color: 0.2, 0.6, 1, 1
    bold: True
    font_size: dp(18)
    size_hint_y: None
    height: dp(50)

<GameScreen>:
    canvas.before:
        Color:
            rgba: 0.1, 0.1, 0.15, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)

        # Header
        BoxLayout:
            size_hint_y: 0.1
            Label:
                text: root.score_text
                font_size: dp(24)
                bold: True
                color: 1, 1, 1, 1
            Button:
                text: "MENU"
                size_hint_x: 0.3
                background_normal: ''
                background_color: 0.3, 0.3, 0.4, 1
                on_release: root.go_to_menu()

        # Board
        AnchorLayout:
            id: board_container
            size_hint_y: 0.6

        # Slots
        GridLayout:
            id: spawn_grid
            cols: 3
            size_hint_y: 0.3
            padding: dp(5)
            spacing: dp(5)

<MenuScreen>:
    canvas.before:
        Color:
            rgba: 0.1, 0.1, 0.15, 1
        Rectangle:
            pos: self.pos
            size: self.size
    
    BoxLayout:
        orientation: 'vertical'
        padding: dp(40)
        spacing: dp(20)
        
        Label:
            text: "BLOCK PUZZLE"
            font_size: dp(40)
            bold: True
        
        SimpleButton:
            text: "Classic Mode"
            on_release: root.start_classic()
            
        SimpleButton:
            text: "Adventure Mode"
            background_color: 1, 0.5, 0, 1
            on_release: root.start_adventure()
"""

class GameCell(Widget):
    """
    Клетка поля. 
    display_color меняется для отображения блока или призрака.
    """
    display_color = ColorProperty(COLORS['grid_empty'])
    is_filled = BooleanProperty(False)

    def set_filled(self, color_name):
        self.is_filled = True
        self.display_color = COLORS[color_name]

    def set_ghost(self, color_name):
        """Включает режим призрака (полупрозрачный цвет)"""
        if not self.is_filled:
            c = COLORS[color_name]
            # Делаем цвет полупрозрачным (Alpha = 0.4)
            self.display_color = (c[0], c[1], c[2], 0.4)

    def reset(self):
        """Возвращает к цвету пустой клетки"""
        if not self.is_filled:
            self.display_color = COLORS['grid_empty']
            
    def clear_block(self):
        """Очистка клетки"""
        self.is_filled = False
        self.display_color = COLORS['grid_empty']

class SingleBlockGraphic:
    """Простой квадрат для отрисовки внутри DragWidget и SlotWidget"""
    def __init__(self, canvas):
        self.canvas = canvas
        with self.canvas:
            self.color = Color(0, 0, 0, 0)
            self.rect = RoundedRectangle(pos=(0, 0), size=(0, 0), radius=[dp(3)])
    
    def update(self, pos, size, rgba):
        self.rect.pos = pos
        self.rect.size = size
        self.color.rgba = rgba
        
    def hide(self):
        self.color.rgba = (0, 0, 0, 0)

class DragWidget(Widget):
    """Виджет, следующий за пальцем."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.blocks = []
        for _ in range(6):
            self.blocks.append(SingleBlockGraphic(self.canvas))
            
        self.current_shape_coords = []
        self.current_color_name = 'blue'
        self.cell_size = 0
        self.active = False
        self.touch_offset = (0, 0)

    def activate(self, shape_coords, color_name, cell_size, touch_pos, offset):
        self.current_shape_coords = shape_coords
        self.current_color_name = color_name
        self.cell_size = cell_size
        self.active = True
        self.touch_offset = offset
        self.update_pos(touch_pos)

    def update_pos(self, touch_pos):
        if not self.active: return
        
        self.x = touch_pos[0] + self.touch_offset[0]
        self.y = touch_pos[1] + self.touch_offset[1]
        
        # Делаем фигуру при перетаскивании чуть прозрачной (0.8)
        raw = COLORS[self.current_color_name]
        rgba = (raw[0], raw[1], raw[2], 0.8)
        
        size = (self.cell_size - GAP*2, self.cell_size - GAP*2)
        
        for i in range(len(self.blocks)):
            if i < len(self.current_shape_coords):
                bx, by = self.current_shape_coords[i]
                px = self.x + bx * self.cell_size + GAP
                py = self.y + by * self.cell_size + GAP
                self.blocks[i].update((px, py), size, rgba)
            else:
                self.blocks[i].hide()

    def hide(self):
        self.active = False
        for b in self.blocks: b.hide()
        self.pos = (-5000, -5000)

class GameBoard(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cells = []
        self.cell_size = dp(40)
        self.grid_layout = GridLayout(cols=GRID_SIZE, spacing=0)
        self.add_widget(self.grid_layout)

    def build_grid(self):
        self.grid_layout.clear_widgets()
        self.cells = []
        temp_cells = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        for y in range(GRID_SIZE - 1, -1, -1):
            for x in range(GRID_SIZE):
                cell = GameCell()
                self.grid_layout.add_widget(cell)
                temp_cells[x][y] = cell
                
        self.cells = temp_cells
        self.bind(pos=self.update_layout, size=self.update_layout)
        Clock.schedule_once(self.update_layout, 0)

    def update_layout(self, *args):
        dim = min(self.width, self.height)
        if dim == 0: return
        self.cell_size = dim / GRID_SIZE
        
        self.grid_layout.size_hint = (None, None)
        self.grid_layout.size = (dim, dim)
        self.grid_layout.pos = (
            self.x + (self.width - dim) / 2,
            self.y + (self.height - dim) / 2
        )

    def get_grid_pos(self, screen_x, screen_y):
        if self.cell_size == 0: return None, None
        gx = int((screen_x - self.grid_layout.x) / self.cell_size)
        gy = int((screen_y - self.grid_layout.y) / self.cell_size)
        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
            return gx, gy
        return None, None

    def clear_preview(self):
        """Очищает призрака"""
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                self.cells[x][y].reset()

    def show_preview(self, shape_coords, start_gx, start_gy, color_name):
        """Показывает призрака"""
        self.clear_preview()
        
        can_place = True
        for bx, by in shape_coords:
            gx, gy = start_gx + bx, start_gy + by
            if not (0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE):
                can_place = False; break
            if self.cells[gx][gy].is_filled:
                can_place = False; break
        
        if can_place:
            for bx, by in shape_coords:
                gx, gy = start_gx + bx, start_gy + by
                self.cells[gx][gy].set_ghost(color_name)
        return can_place

    def place_shape(self, shape_coords, start_gx, start_gy, color_name):
        for bx, by in shape_coords:
            self.cells[start_gx + bx][start_gy + by].set_filled(color_name)

class SlotWidget(Widget):
    """Слот с фигурой."""
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game = game_screen
        self.blocks = []
        for _ in range(6):
            self.blocks.append(SingleBlockGraphic(self.canvas))
            
        self.shape_coords = []
        self.color_name = 'blue'
        self.is_filled = False
        self.preview_scale = 0.6
        self.bind(pos=self.update_visuals, size=self.update_visuals)

    def set_shape(self, shape_data):
        self.shape_coords = shape_data['coords']
        self.color_name = shape_data['color']
        self.is_filled = True
        self.update_visuals()

    def set_empty(self):
        self.is_filled = False
        for b in self.blocks: b.hide()

    def update_visuals(self, *args):
        if not self.is_filled:
            for b in self.blocks: b.hide()
            return

        cell_size = (Window.width / 10) * self.preview_scale
        
        max_x = max(c[0] for c in self.shape_coords)
        max_y = max(c[1] for c in self.shape_coords)
        w = (max_x + 1) * cell_size
        h = (max_y + 1) * cell_size
        
        start_x = self.center_x - w / 2
        start_y = self.center_y - h / 2
        
        rgba = COLORS[self.color_name]
        size = (cell_size - GAP*2, cell_size - GAP*2)
        count = len(self.shape_coords)
        
        for i in range(len(self.blocks)):
            if i < count:
                bx, by = self.shape_coords[i]
                px = start_x + bx * cell_size + GAP
                py = start_y + by * cell_size + GAP
                self.blocks[i].update((px, py), size, rgba)
            else:
                self.blocks[i].hide()

    def on_touch_down(self, touch):
        if self.is_filled and self.collide_point(*touch.pos):
            touch.grab(self)
            
            real_cell_size = self.game.board.cell_size
            if real_cell_size == 0: real_cell_size = dp(40)
            
            cell_size_p = (Window.width / 10) * self.preview_scale
            max_x = max(c[0] for c in self.shape_coords)
            w_p = (max_x + 1) * cell_size_p
            
            # Смещение, чтобы палец был по центру фигуры
            offset = (-w_p/2, dp(50))
            
            self.game.drag_widget.activate(
                self.shape_coords, 
                self.color_name, 
                real_cell_size, 
                touch.pos,
                offset
            )
            for b in self.blocks: b.hide()
            return True
        return super().on_touch_down(touch)
        
    def on_touch_move(self, touch):
        if touch.grab_current is self:
            drag = self.game.drag_widget
            drag.update_pos(touch.pos)
            
            # --- GHOST LOGIC ---
            check_x = drag.x + drag.cell_size / 2
            check_y = drag.y + drag.cell_size / 2
            
            gx, gy = self.game.board.get_grid_pos(check_x, check_y)
            
            if gx is not None and gy is not None:
                self.game.board.show_preview(self.shape_coords, gx, gy, self.color_name)
            else:
                self.game.board.clear_preview()
            
            return True
        return super().on_touch_move(touch)
        
    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            
            drag = self.game.drag_widget
            check_x = drag.x + drag.cell_size / 2
            check_y = drag.y + drag.cell_size / 2
            
            gx, gy = self.game.board.get_grid_pos(check_x, check_y)
            success = False
            
            if gx is not None and gy is not None:
                self.game.board.clear_preview()
                
                can_place = True
                for bx, by in self.shape_coords:
                    cgx, cgy = gx + bx, gy + by
                    if not (0 <= cgx < GRID_SIZE and 0 <= cgy < GRID_SIZE):
                        can_place = False; break
                    if self.game.board.cells[cgx][cgy].is_filled:
                        can_place = False; break
                
                if can_place:
                    self.game.board.place_shape(self.shape_coords, gx, gy, self.color_name)
                    self.game.check_lines()
                    self.game.process_score(len(self.shape_coords))
                    success = True

            drag.hide()
            self.game.board.clear_preview()
            
            if success:
                self.set_empty()
                self.game.on_shape_placed()
            else:
                self.update_visuals()
            
            return True
        return super().on_touch_up(touch)

class GameScreen(Screen):
    score = NumericProperty(0)
    score_text = StringProperty("Score: 0")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drag_widget = DragWidget()
        self.board = GameBoard()
        self.slots = []
        self.mode = 'classic'
        self.target_score = 100

    def on_enter(self):
        if not self.ids.board_container.children:
            self.ids.board_container.add_widget(self.board)
            self.board.build_grid()
            
            for _ in range(3):
                anchor = AnchorLayout(anchor_x='center', anchor_y='center')
                slot = SlotWidget(self)
                self.slots.append(slot)
                anchor.add_widget(slot)
                self.ids.spawn_grid.add_widget(anchor)
            
            Window.add_widget(self.drag_widget)
            
        self.start_game()

    def go_to_menu(self):
        self.manager.current = 'menu'

    def start_game(self):
        for row in self.board.cells:
            for cell in row: cell.clear_block()
        
        self.score = 0
        self.update_score_label()
        for slot in self.slots: slot.set_empty()
        self.spawn_new_shapes()

    def update_score_label(self):
        if self.mode == 'adventure':
            self.score_text = f"Score: {self.score} / {self.target_score}"
        else:
            self.score_text = f"Score: {self.score}"

    def spawn_new_shapes(self):
        for slot in self.slots:
            slot.set_shape(random.choice(SHAPES_DEF))
        self.check_game_over()

    def on_shape_placed(self):
        if all(not s.is_filled for s in self.slots):
            Clock.schedule_once(lambda dt: self.spawn_new_shapes(), 0.1)
        else:
            self.check_game_over()

    def check_lines(self):
        lines_x, lines_y = [], []
        
        for y in range(GRID_SIZE):
            if all(self.board.cells[x][y].is_filled for x in range(GRID_SIZE)):
                lines_y.append(y)
        for x in range(GRID_SIZE):
            if all(self.board.cells[x][y].is_filled for y in range(GRID_SIZE)):
                lines_x.append(x)
                
        if lines_x or lines_y:
            for y in lines_y:
                for x in range(GRID_SIZE): self.board.cells[x][y].clear_block()
            for x in lines_x:
                for y in range(GRID_SIZE): self.board.cells[x][y].clear_block()
            
            points = (len(lines_x) + len(lines_y)) * 10
            self.process_score(points)

    def process_score(self, points):
        self.score += points
        self.update_score_label()
        if self.mode == 'adventure' and self.score >= self.target_score:
             Clock.schedule_once(lambda dt: self.level_up(), 0.5)

    def level_up(self):
        self.target_score = int(self.target_score * 1.5)
        self.score = 0
        for row in self.board.cells:
            for cell in row: cell.clear_block()
        self.update_score_label()
        self.spawn_new_shapes()
        self.show_popup("LEVEL COMPLETE", "Next Level!", color=(0.2, 0.8, 0.4, 1))

    def check_game_over(self):
        active_slots = [s for s in self.slots if s.is_filled]
        if not active_slots: return

        can_move = False
        for slot in active_slots:
            for x in range(GRID_SIZE):
                for y in range(GRID_SIZE):
                    fits = True
                    for bx, by in slot.shape_coords:
                        gx, gy = x + bx, y + by
                        if not (0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE):
                            fits = False; break
                        if self.board.cells[gx][gy].is_filled:
                            fits = False; break
                    if fits: can_move = True; break
                if can_move: break
            if can_move: break
        
        if not can_move:
            self.show_popup("GAME OVER", f"Score: {self.score}", restart=True)

    def show_popup(self, title, msg, restart=False, color=(1, 0.3, 0.3, 1)):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        content.add_widget(Label(text=msg, font_size=dp(24)))
        btn = Button(text="OK", size_hint_y=None, height=dp(50), background_color=color)
        content.add_widget(btn)
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4), 
                      auto_dismiss=False, separator_color=color, title_color=color)
        def on_btn(instance):
            popup.dismiss()
            if restart: self.start_game()
        btn.bind(on_release=on_btn)
        popup.open()

class MenuScreen(Screen):
    def start_classic(self):
        self.manager.get_screen('game').mode = 'classic'
        self.manager.current = 'game'
    def start_adventure(self):
        self.manager.get_screen('game').mode = 'adventure'
        self.manager.current = 'game'

class BlockPuzzleApp(App):
    def build(self):
        Builder.load_string(KV)
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == '__main__':
    BlockPuzzleApp().run()