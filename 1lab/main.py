import pygame
import sys
from enum import Enum
from typing import List, Tuple, Optional
from abc import ABC, abstractmethod


class GameMode(Enum):
    """Режимы игры"""
    MENU = "menu"
    CHESS = "chess"
    CHECKERS = "checkers"


class Color(Enum):
    """Цвета фигур"""
    WHITE = "white"
    BLACK = "black"


class Move:
    """Класс для хранения информации о ходе (для отката)"""
    def __init__(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], 
                 piece: Optional['Piece'] = None,
                 captured_piece: Optional['Piece'] = None, 
                 captured_en_passant: Optional['Piece'] = None,
                 last_move_for_pawn: Optional[Tuple[int, int]] = None,
                 piece_was_moved: bool = False):
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.piece = piece  # Исходная фигура (до хода)
        self.captured_piece = captured_piece  # Фигура, которая была на целевой позиции
        self.captured_en_passant = captured_en_passant  # Пешка, съедена при взятии на проходе
        self.last_move_for_pawn = last_move_for_pawn  # Для взятия на проходе
        self.piece_was_moved = piece_was_moved  # Был ли у фигуры уже сделан ход


class PieceType(Enum):
    """Типы шахматных фигур"""
    PAWN = "♙" #Пешка
    ROOK = "♖" #Ладья
    KNIGHT = "♘" #Конь
    BISHOP = "♗" #Слон
    QUEEN = "♕" #Королева
    KING = "♔" #Король


class Piece(ABC):
    """Базовый класс для всех шахматных фигур"""
    
    def __init__(self, color: Color, position: Tuple[int, int], piece_type: PieceType):
        self.color = color
        self.position = position  # (row, col)
        self.piece_type = piece_type
        self.has_moved = False  # Для фигур, которым это важно (король, ладья)
    
    @abstractmethod
    def get_possible_moves(self, board: 'Board') -> List[Tuple[int, int]]:
        """Получить список возможных ходов для фигуры"""
        pass
    
    def is_valid_position(self, row: int, col: int) -> bool:
        """Проверить, находится ли позиция в пределах доски"""
        return 0 <= row < 8 and 0 <= col < 8
    
    def get_symbol(self) -> str:
        """Получить символ фигуры"""
        return self.piece_type.value
    
    def __repr__(self) -> str:
        """Получить строковое представление фигуры для отладки"""
        color_str = "W" if self.color == Color.WHITE else "B"
        return f"{color_str}{self.piece_type.name[0]}"


class Pawn(Piece):
    """Класс пешки"""
    
    def __init__(self, color: Color, position: Tuple[int, int]):
        super().__init__(color, position, PieceType.PAWN)
    
    def get_possible_moves(self, board: 'Board') -> List[Tuple[int, int]]:
        moves = []
        row, col = self.position
        direction = -1 if self.color == Color.WHITE else 1  # Белые вверх, черные вниз
        
        # Ход на одну клетку вперед
        new_row = row + direction
        if board.is_valid_position(new_row, col) and board.is_empty(new_row, col):
            moves.append((new_row, col))
            
            # Первый ход на две клетки
            start_row = 6 if self.color == Color.WHITE else 1
            if row == start_row:
                new_row_2 = row + 2 * direction
                if board.is_empty(new_row_2, col):
                    moves.append((new_row_2, col))
        
        # Диагональные взятия
        for new_col in [col - 1, col + 1]:
            new_row = row + direction
            if (board.is_valid_position(new_row, new_col) and 
                board.has_piece(new_row, new_col) and 
                board.get_piece(new_row, new_col).color != self.color):
                moves.append((new_row, new_col))
        
        # Взятие на проходе
        if board.last_pawn_move:
            enemy_pawn_row, enemy_pawn_col = board.last_pawn_move
            # Проверить, находится ли враждебная пешка рядом и только что сделала ход на 2 клетки
            if enemy_pawn_row == row and abs(enemy_pawn_col - col) == 1:
                enemy_piece = board.get_piece(enemy_pawn_row, enemy_pawn_col)
                if enemy_piece and isinstance(enemy_piece, Pawn) and enemy_piece.color != self.color:
                    capture_row = enemy_pawn_row + direction
                    if board.is_valid_position(capture_row, enemy_pawn_col) and board.is_empty(capture_row, enemy_pawn_col):
                        moves.append((capture_row, enemy_pawn_col))
        
        return moves


class Rook(Piece):
    """Класс ладьи"""
    
    def __init__(self, color: Color, position: Tuple[int, int]):
        super().__init__(color, position, PieceType.ROOK)
    
    def get_possible_moves(self, board: 'Board') -> List[Tuple[int, int]]:
        moves = []
        row, col = self.position
        
        # Движение по горизонтали и вертикали
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            new_row, new_col = row + dr, col + dc
            while board.is_valid_position(new_row, new_col):
                if board.is_empty(new_row, new_col):
                    moves.append((new_row, new_col))
                elif board.get_piece(new_row, new_col).color != self.color:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
                new_row += dr
                new_col += dc
        
        return moves


class Knight(Piece):
    """Класс коня"""
    
    def __init__(self, color: Color, position: Tuple[int, int]):
        super().__init__(color, position, PieceType.KNIGHT)
    
    def get_possible_moves(self, board: 'Board') -> List[Tuple[int, int]]:
        moves = []
        row, col = self.position
        
        # L-образные ходы коня
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        
        for dr, dc in knight_moves:
            new_row, new_col = row + dr, col + dc
            if board.is_valid_position(new_row, new_col):
                if board.is_empty(new_row, new_col) or board.get_piece(new_row, new_col).color != self.color:
                    moves.append((new_row, new_col))
        
        return moves


class Bishop(Piece):
    """Класс слона"""
    
    def __init__(self, color: Color, position: Tuple[int, int]):
        super().__init__(color, position, PieceType.BISHOP)
    
    def get_possible_moves(self, board: 'Board') -> List[Tuple[int, int]]:
        moves = []
        row, col = self.position
        
        # Диагональные движения
        for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            new_row, new_col = row + dr, col + dc
            while board.is_valid_position(new_row, new_col):
                if board.is_empty(new_row, new_col):
                    moves.append((new_row, new_col))
                elif board.get_piece(new_row, new_col).color != self.color:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
                new_row += dr
                new_col += dc
        
        return moves


class Queen(Piece):
    """Класс королевы"""
    
    def __init__(self, color: Color, position: Tuple[int, int]):
        super().__init__(color, position, PieceType.QUEEN)
    
    def get_possible_moves(self, board: 'Board') -> List[Tuple[int, int]]:
        moves = []
        row, col = self.position
        
        # Комбинация ходов ладьи и слона
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0), 
                       (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            new_row, new_col = row + dr, col + dc
            while board.is_valid_position(new_row, new_col):
                if board.is_empty(new_row, new_col):
                    moves.append((new_row, new_col))
                elif board.get_piece(new_row, new_col).color != self.color:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
                new_row += dr
                new_col += dc
        
        return moves


class King(Piece):
    """Класс короля"""
    
    def __init__(self, color: Color, position: Tuple[int, int]):
        super().__init__(color, position, PieceType.KING)
    
    def get_possible_moves(self, board: 'Board') -> List[Tuple[int, int]]:
        moves = []
        row, col = self.position
        
        # Король движется на одну клетку в любом направлении
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                new_row, new_col = row + dr, col + dc
                if board.is_valid_position(new_row, new_col):
                    if board.is_empty(new_row, new_col) or board.get_piece(new_row, new_col).color != self.color:
                        moves.append((new_row, new_col))
        
        return moves


class Board:
    """Класс шахматной доски"""
    
    def __init__(self):
        self.grid: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.move_history: List[Move] = []  # История всех ходов
        self.last_pawn_move: Optional[Tuple[int, int]] = None  # Для взятия на проходе
        self.initialize_pieces()
    
    def initialize_pieces(self):
        """Инициализировать начальную расстановку фигур"""
        # Черные фигуры (верх доски)
        self.grid[0][0] = Rook(Color.BLACK, (0, 0))
        self.grid[0][1] = Knight(Color.BLACK, (0, 1))
        self.grid[0][2] = Bishop(Color.BLACK, (0, 2))
        self.grid[0][3] = Queen(Color.BLACK, (0, 3))
        self.grid[0][4] = King(Color.BLACK, (0, 4))
        self.grid[0][5] = Bishop(Color.BLACK, (0, 5))
        self.grid[0][6] = Knight(Color.BLACK, (0, 6))
        self.grid[0][7] = Rook(Color.BLACK, (0, 7))
        
        for col in range(8):
            self.grid[1][col] = Pawn(Color.BLACK, (1, col))
        
        # Белые фигуры (низ доски)
        for col in range(8):
            self.grid[6][col] = Pawn(Color.WHITE, (6, col))
        
        self.grid[7][0] = Rook(Color.WHITE, (7, 0))
        self.grid[7][1] = Knight(Color.WHITE, (7, 1))
        self.grid[7][2] = Bishop(Color.WHITE, (7, 2))
        self.grid[7][3] = Queen(Color.WHITE, (7, 3))
        self.grid[7][4] = King(Color.WHITE, (7, 4))
        self.grid[7][5] = Bishop(Color.WHITE, (7, 5))
        self.grid[7][6] = Knight(Color.WHITE, (7, 6))
        self.grid[7][7] = Rook(Color.WHITE, (7, 7))
    
    def is_valid_position(self, row: int, col: int) -> bool:
        """Проверить валидность позиции"""
        return 0 <= row < 8 and 0 <= col < 8
    
    def is_empty(self, row: int, col: int) -> bool:
        """Проверить, пуста ли клетка"""
        if not self.is_valid_position(row, col):
            return False
        return self.grid[row][col] is None
    
    def has_piece(self, row: int, col: int) -> bool:
        """Проверить, есть ли фигура на позиции"""
        if not self.is_valid_position(row, col):
            return False
        return self.grid[row][col] is not None
    
    def get_piece(self, row: int, col: int) -> Optional[Piece]:
        """Получить фигуру на позиции"""
        if self.is_valid_position(row, col):
            return self.grid[row][col]
        return None
    
    def move_piece(self, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Переместить фигуру"""
        piece = self.get_piece(from_row, from_col)
        if piece is None:
            return False
        
        # Проверить, возможен ли этот ход
        if (to_row, to_col) not in piece.get_possible_moves(self):
            return False
        
        # Сохранить захваченную фигуру
        captured_piece = self.get_piece(to_row, to_col)
        
        # Обработка взятия на проходе для пешек
        captured_en_passant = None
        if isinstance(piece, Pawn) and captured_piece is None and to_col != from_col:
            # Это взятие на проходе
            enemy_pawn_row = from_row
            captured_en_passant = self.get_piece(enemy_pawn_row, to_col)
            self.grid[enemy_pawn_row][to_col] = None
        
        # Сохранить последний ход пешки для взятия на проходе
        last_pawn_move = self.last_pawn_move
        if isinstance(piece, Pawn):
            # Проверить, была ли это пешка, которая давно не двигалась
            if abs(to_row - from_row) == 2:
                # Пешка сделала ход на 2 клетки
                self.last_pawn_move = (to_row, to_col)
            else:
                self.last_pawn_move = None
        else:
            self.last_pawn_move = None
        
        # Сохранить было ли у фигуры уже сделан ход
        piece_was_moved = piece.has_moved
        
        # Выполнить ход
        original_piece = piece  # Сохраняем ссылку на оригинальную фигуру
        self.grid[to_row][to_col] = piece
        self.grid[from_row][from_col] = None
        piece.position = (to_row, to_col)
        piece.has_moved = True
        
        # Обработка превращения пешки
        if isinstance(piece, Pawn):
            if (piece.color == Color.WHITE and to_row == 0) or (piece.color == Color.BLACK and to_row == 7):
                # Пешка достигла конца доски - превращается в королеву
                new_piece = Queen(piece.color, (to_row, to_col))
                self.grid[to_row][to_col] = new_piece
        
        # Сохранить ход в историю
        move = Move((from_row, from_col), (to_row, to_col), 
                   original_piece, captured_piece, captured_en_passant, last_pawn_move, piece_was_moved)
        self.move_history.append(move)
        
        return True
    
    def undo_move(self) -> bool:
        """Отменить последний ход"""
        if not self.move_history:
            return False
        
        move = self.move_history.pop()
        
        # Очистить целевую позицию
        self.grid[move.to_pos[0]][move.to_pos[1]] = None
        
        # Вернуть исходную фигуру на исходную позицию
        if move.piece:
            self.grid[move.from_pos[0]][move.from_pos[1]] = move.piece
            move.piece.position = move.from_pos
            move.piece.has_moved = move.piece_was_moved  # Восстановить исходное состояние
        
        # Вернуть захваченную фигуру (если была съедена на целевой позиции)
        if move.captured_piece:
            self.grid[move.to_pos[0]][move.to_pos[1]] = move.captured_piece
        
        # Вернуть захваченную пешку (если было взятие на проходе)
        if move.captured_en_passant:
            # Пешка была съедена на исходной позиции врага
            enemy_row = move.from_pos[0]  # Строка исходной позиции текущей пешки
            enemy_col = move.to_pos[1]    # Столбец целевой позиции
            self.grid[enemy_row][enemy_col] = move.captured_en_passant
        
        # Вернуть последний ход пешки
        self.last_pawn_move = move.last_move_for_pawn
        
        return True
    
    def get_all_pieces(self, color: Color) -> List[Piece]:
        """Получить все фигуры определенного цвета"""
        pieces = []
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece and piece.color == color:
                    pieces.append(piece)
        return pieces
    
    def is_king_in_check(self, king_color: Color) -> bool:
        """Проверить, находится ли король под шахом"""
        # Найти короля
        king_pos = None
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece and isinstance(piece, King) and piece.color == king_color:
                    king_pos = (row, col)
                    break
            if king_pos:
                break
        
        if not king_pos:
            return False
        
        # Проверить, может ли любая вражеская фигура захватить короля
        enemy_color = Color.BLACK if king_color == Color.WHITE else Color.WHITE
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece and piece.color == enemy_color:
                    if king_pos in piece.get_possible_moves(self):
                        return True
        
        return False


class GameApplication:
    """Главное приложение - меню и управление игрой"""
    def __init__(self):
        pygame.init()
        
        self.width = 1000
        self.height = 800
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Шахматы и Шашки")
        
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 64)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        
        self.current_mode = GameMode.MENU
        self.game = None
        self.running = True
        
        # Кнопки меню
        self.chess_button = pygame.Rect(150, 250, 300, 150)
        self.checkers_button = pygame.Rect(550, 250, 300, 150)
    
    def draw_menu(self):
        """Нарисовать меню выбора"""
        self.screen.fill((40, 40, 60))
        
        # Заголовок
        title = self.font_large.render("ВЫБЕРИТЕ ИГРУ", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.width // 2, 80))
        self.screen.blit(title, title_rect)
        
        # Кнопка Шахматы
        pygame.draw.rect(self.screen, (100, 100, 200), self.chess_button)
        pygame.draw.rect(self.screen, (200, 200, 255), self.chess_button, 3)
        chess_text = self.font_medium.render("ШАХМАТЫ", True, (255, 255, 255))
        chess_rect = chess_text.get_rect(center=self.chess_button.center)
        self.screen.blit(chess_text, chess_rect)
        
        # Кнопка Шашки
        pygame.draw.rect(self.screen, (200, 100, 100), self.checkers_button)
        pygame.draw.rect(self.screen, (255, 200, 200), self.checkers_button, 3)
        checkers_text = self.font_medium.render("ШАШКИ", True, (255, 255, 255))
        checkers_rect = checkers_text.get_rect(center=self.checkers_button.center)
        self.screen.blit(checkers_text, checkers_rect)
    
    def handle_menu_click(self, pos: Tuple[int, int]):
        """Обработать клик в меню"""
        if self.chess_button.collidepoint(pos):
            self.current_mode = GameMode.CHESS
            self.game = ChessGame()  # Создаст свой экран нужного размера
        elif self.checkers_button.collidepoint(pos):
            self.current_mode = GameMode.CHECKERS
            self.game = CheckersGame()  # Создаст свой экран нужного размера
    
    def run(self):
        """Главный цикл приложения"""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.current_mode == GameMode.MENU:
                        self.handle_menu_click(event.pos)
            
            if self.current_mode == GameMode.MENU:
                self.draw_menu()
                pygame.display.flip()
                self.clock.tick(60)
            elif self.game:
                self.game.run()
                self.current_mode = GameMode.MENU
                self.game = None
        
        pygame.quit()
        sys.exit()


class ChessGame:
    """Главный класс игры"""
    
    def __init__(self, screen=None):
        self.board_size = 800
        self.panel_width = 200
        self.width = self.board_size + self.panel_width
        self.height = 800
        self.square_size = self.board_size // 8
        
        self.screen = screen if screen else pygame.display.set_mode((self.width, self.height))
        if not screen:
            pygame.display.set_caption("Шахматы")
        
        self.clock = pygame.time.Clock()
        self.board = Board()
        
        # Шрифты
        self.font = pygame.font.Font(None, 36)
        try:
            self.piece_font = pygame.font.SysFont("segoe ui symbol", 72)
        except:
            try:
                self.piece_font = pygame.font.SysFont("arial unicode ms", 72)
            except:
                self.piece_font = pygame.font.Font(None, 72)
        
        # Цвета доски
        self.light_color = (240, 217, 181)  # Светлый цвет
        self.dark_color = (181, 136, 99)    # Тёмный цвет
        self.highlight_color = (186, 202, 43)
        self.move_highlight_color = (255, 255, 0)
        self.panel_color = (60, 80, 60)     # Цвет панели
        self.white_player_color = (200, 200, 255)  # Светло-синий для белых
        self.black_player_color = (255, 150, 150)  # Светло-красный для чёрных
        
        # Состояние игры
        self.current_player = Color.WHITE
        self.selected_piece = None
        self.selected_position = None
        self.possible_moves = []
        self.running = True
        self.undo_button = pygame.Rect(0, 0, 0, 0)  # Инициализируем кнопку (будет обновлена в draw_panel)
        self.menu_button = pygame.Rect(0, 0, 0, 0)  # Кнопка меню
        
        # Таймер
        self.start_time = pygame.time.get_ticks()
        self.white_time = 600  # 10 минут в секундах
        self.black_time = 600
        self.last_time_update = self.start_time
    
    def handle_click(self, pos: Tuple[int, int]):
        """Обработать клик мыши"""
        # Проверить, был ли клик на кнопку Меню
        if hasattr(self, 'menu_button') and self.menu_button.collidepoint(pos):
            self.running = False
            return
        
        # Проверить, был ли клик на кнопку Undo
        if hasattr(self, 'undo_button') and self.undo_button.collidepoint(pos):
            # Отменить последний ход
            if self.board.undo_move():
                # Вернулись на ход назад, нужно переключить игрока
                self.current_player = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
                self.selected_piece = None
                self.selected_position = None
                self.possible_moves = []
            return
        
        # Игнорируем клики на панели
        if pos[0] >= self.board_size:
            return
        
        col = pos[0] // self.square_size
        row = pos[1] // self.square_size
        
        if not self.board.is_valid_position(row, col):
            return
        
        # Если клик на уже выбранную фигуру - отменить выбор
        if self.selected_position == (row, col):
            self.selected_piece = None
            self.selected_position = None
            self.possible_moves = []
            return
        
        # Если клик на возможный ход
        if (row, col) in self.possible_moves:
            self.board.move_piece(self.selected_position[0], self.selected_position[1], row, col)
            self.current_player = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
            self.selected_piece = None
            self.selected_position = None
            self.possible_moves = []
            return
        
        # Выбрать новую фигуру
        piece = self.board.get_piece(row, col)
        if piece and piece.color == self.current_player:
            self.selected_piece = piece
            self.selected_position = (row, col)
            self.possible_moves = piece.get_possible_moves(self.board)
        else:
            self.selected_piece = None
            self.selected_position = None
            self.possible_moves = []
    
    def get_threatened_pieces(self) -> List[Tuple[int, int]]:
        """Получить список позиций фигур текущего игрока, которые под угрозой"""
        threatened = []
        enemy_color = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
        
        # Пройти по всем фигурам врага
        for row in range(8):
            for col in range(8):
                enemy_piece = self.board.get_piece(row, col)
                if enemy_piece and enemy_piece.color == enemy_color:
                    # Получить все возможные ходы этой фигуры врага
                    enemy_moves = enemy_piece.get_possible_moves(self.board)
                    # Добавить все позиции фигур текущего игрока в списке ходов врага
                    for move_pos in enemy_moves:
                        target = self.board.get_piece(move_pos[0], move_pos[1])
                        if target and target.color == self.current_player:
                            threatened.append(move_pos)
        
        return threatened
    
    def draw_board(self):
        """Нарисовать доску"""
        threatened_positions = self.get_threatened_pieces()
        
        for row in range(8):
            for col in range(8):
                rect = pygame.Rect(col * self.square_size, row * self.square_size,
                                 self.square_size, self.square_size)
                
                # Определить цвет клетки
                if (row + col) % 2 == 0:
                    pygame.draw.rect(self.screen, self.light_color, rect)
                else:
                    pygame.draw.rect(self.screen, self.dark_color, rect)
                
                # Выделить угрожаемые фигуры оранжевым цветом
                if (row, col) in threatened_positions:
                    pygame.draw.rect(self.screen, (255, 165, 0), rect, 3)
                
                # Выделить выбранную фигуру
                if self.selected_position == (row, col):
                    pygame.draw.rect(self.screen, self.highlight_color, rect, 4)
                
                # Выделить возможные ходы
                if (row, col) in self.possible_moves:
                    # Проверить, это атака или обычный ход
                    target_piece = self.board.get_piece(row, col)
                    if target_piece and target_piece.color != self.current_player:
                        # Это атака - красное выделение
                        pygame.draw.rect(self.screen, (255, 0, 0), rect, 3)
                    else:
                        # Обычный ход - зелёное выделение
                        pygame.draw.rect(self.screen, (0, 200, 0), rect, 3)
    
    def draw_pieces(self):
        """Нарисовать фигуры с мягким outline"""
        outline_width = 1
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece:
                    x = col * self.square_size + self.square_size // 2
                    y = row * self.square_size + self.square_size // 2
                    
                    # Выбрать цвет фигуры
                    piece_color = (255, 255, 255) if piece.color == Color.WHITE else (0, 0, 0)
                    
                    # Определить цвет клетки для мягкого outline
                    if (row + col) % 2 == 0:
                        outline_color = self.light_color
                    else:
                        outline_color = self.dark_color
                    
                    # Рисуем мягкий outline
                    outline_text = self.piece_font.render(piece.get_symbol(), True, outline_color)
                    for dx in range(-outline_width, outline_width + 1):
                        for dy in range(-outline_width, outline_width + 1):
                            if dx != 0 or dy != 0:
                                outline_rect = outline_text.get_rect(center=(x + dx, y + dy))
                                self.screen.blit(outline_text, outline_rect)
                    
                    # Рисуем саму фигуру
                    text = self.piece_font.render(piece.get_symbol(), True, piece_color)
                    text_rect = text.get_rect(center=(x, y))
                    self.screen.blit(text, text_rect)
    
    def update_timer(self):
        """Обновить таймер для текущего игрока"""
        current_time = pygame.time.get_ticks()
        elapsed = (current_time - self.last_time_update) // 1000
        
        if elapsed >= 1:
            if self.current_player == Color.WHITE:
                self.white_time = max(0, self.white_time - 1)
            else:
                self.black_time = max(0, self.black_time - 1)
            self.last_time_update = current_time
    
    def format_time(self, seconds: int) -> str:
        """Форматировать время в минуты:секунды"""
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"
    
    def draw_panel(self):
        """Нарисовать панель с информацией о игре"""
        panel_rect = pygame.Rect(self.board_size, 0, self.panel_width, self.height)
        pygame.draw.rect(self.screen, self.panel_color, panel_rect)
        pygame.draw.line(self.screen, (255, 255, 255), 
                        (self.board_size, 0), (self.board_size, self.height), 2)
        
        # Отступы и размеры
        y_offset = 30
        
        # Заголовок
        title_font = pygame.font.Font(None, 32)
        title = title_font.render("Шахматы", True, (255, 255, 255))
        self.screen.blit(title, (self.board_size + 20, y_offset))
        
        y_offset += 50
        
        # Белые
        small_font = pygame.font.Font(None, 24)
        white_label = small_font.render("Белые:", True, (255, 255, 255))
        self.screen.blit(white_label, (self.board_size + 15, y_offset))
        
        white_box = pygame.Rect(self.board_size + 10, y_offset + 25, self.panel_width - 20, 50)
        if self.current_player == Color.WHITE:
            pygame.draw.rect(self.screen, self.white_player_color, white_box)
            pygame.draw.rect(self.screen, (255, 255, 255), white_box, 3)
        else:
            pygame.draw.rect(self.screen, (100, 100, 140), white_box)
            pygame.draw.rect(self.screen, (200, 200, 200), white_box, 1)
        
        white_time_text = title_font.render(self.format_time(max(0, self.white_time)), True, (0, 0, 0))
        white_rect = white_time_text.get_rect(center=(self.board_size + self.panel_width // 2, y_offset + 52))
        self.screen.blit(white_time_text, white_rect)
        
        y_offset += 100
        
        # Черные
        black_label = small_font.render("Черные:", True, (255, 255, 255))
        self.screen.blit(black_label, (self.board_size + 15, y_offset))
        
        black_box = pygame.Rect(self.board_size + 10, y_offset + 25, self.panel_width - 20, 50)
        if self.current_player == Color.BLACK:
            pygame.draw.rect(self.screen, self.black_player_color, black_box)
            pygame.draw.rect(self.screen, (255, 255, 255), black_box, 3)
        else:
            pygame.draw.rect(self.screen, (140, 80, 80), black_box)
            pygame.draw.rect(self.screen, (200, 200, 200), black_box, 1)
        
        black_time_text = title_font.render(self.format_time(max(0, self.black_time)), True, (0, 0, 0))
        black_rect = black_time_text.get_rect(center=(self.board_size + self.panel_width // 2, y_offset + 52))
        self.screen.blit(black_time_text, black_rect)
        
        # Кнопка Undo
        y_offset += 100
        self.undo_button = pygame.Rect(self.board_size + 10, y_offset, self.panel_width - 20, 40)
        pygame.draw.rect(self.screen, (100, 150, 200), self.undo_button)
        pygame.draw.rect(self.screen, (255, 255, 255), self.undo_button, 2)
        
        undo_text = small_font.render("Ход назад", True, (255, 255, 255))
        undo_rect = undo_text.get_rect(center=(self.board_size + self.panel_width // 2, y_offset + 20))
        self.screen.blit(undo_text, undo_rect)
        
        # Кнопка Меню
        y_offset += 55
        self.menu_button = pygame.Rect(self.board_size + 10, y_offset, self.panel_width - 20, 40)
        pygame.draw.rect(self.screen, (150, 100, 150), self.menu_button)
        pygame.draw.rect(self.screen, (255, 255, 255), self.menu_button, 2)
        
        menu_text = small_font.render("МЕНЮ", True, (255, 255, 255))
        menu_rect = menu_text.get_rect(center=(self.board_size + self.panel_width // 2, y_offset + 20))
        self.screen.blit(menu_text, menu_rect)
        
        # Инфо о шахе
        y_offset += 55
        if self.board.is_king_in_check(self.current_player):
            check_text = small_font.render("ШАХ!", True, (255, 100, 100))
            self.screen.blit(check_text, (self.board_size + 15, y_offset))
    
    def run(self):
        """Главный цикл игры"""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
            
            # Очистить экран
            self.screen.fill((240, 240, 240))
            
            # Обновить таймеры
            self.update_timer()
            
            # Нарисовать элементы
            self.draw_board()
            self.draw_pieces()
            self.draw_panel()
            
            # Обновить экран
            pygame.display.flip()
            self.clock.tick(60)


class CheckersPiece:
    """Класс для шашечной фигуры"""
    def __init__(self, color: Color, row: int, col: int, is_king: bool = False):
        self.color = color
        self.row = row
        self.col = col
        self.is_king = is_king
    
    def get_possible_moves(self, board: 'CheckersBoard') -> List[Tuple[int, int]]:
        """Получить возможные ходы"""
        moves = []
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        # Если это обычная пешка, она может ходить только вперёд
        if not self.is_king:
            if self.color == Color.WHITE:
                directions = [(-1, -1), (-1, 1)]  # Вверх
            else:
                directions = [(1, -1), (1, 1)]  # Вниз
        
        # Обычные ходы
        for dr, dc in directions:
            new_row, new_col = self.row + dr, self.col + dc
            if board.is_valid_position(new_row, new_col) and board.is_empty(new_row, new_col):
                moves.append((new_row, new_col))
        
        # Ходы с съеданием (на 2 клетки)
        capture_directions = [(-2, -2), (-2, 2), (2, -2), (2, 2)]
        
        # Для обычной пешки - только вперёд бить
        if not self.is_king:
            if self.color == Color.WHITE:
                capture_directions = [(-2, -2), (-2, 2)]  # Вверх
            else:
                capture_directions = [(2, -2), (2, 2)]  # Вниз
        
        for dr, dc in capture_directions:
            new_row, new_col = self.row + dr, self.col + dc
            mid_row, mid_col = self.row + dr // 2, self.col + dc // 2
            
            if board.is_valid_position(new_row, new_col) and board.is_empty(new_row, new_col):
                enemy = board.get_piece(mid_row, mid_col)
                if enemy and enemy.color != self.color:
                    moves.append((new_row, new_col))
        
        return moves
    
    def get_symbol(self) -> str:
        """Получить символ фигуры"""
        if self.is_king:
            return "♚" if self.color == Color.WHITE else "♛"
        return "●"


class CheckersBoard:
    """Класс шашечной доски"""
    def __init__(self):
        self.grid: List[List[Optional[CheckersPiece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.move_history: List[Tuple[Tuple[int, int], Tuple[int, int], Optional[CheckersPiece]]] = []
        self.initialize_pieces()
    
    def initialize_pieces(self):
        """Инициализировать расстановку"""
        # Чёрные пешки (вверху)
        for row in [0, 1, 2]:
            for col in range(8):
                if (row + col) % 2 == 1:  # Только на чёрных клетках
                    self.grid[row][col] = CheckersPiece(Color.BLACK, row, col)
        
        # Белые пешки (внизу)
        for row in [5, 6, 7]:
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.grid[row][col] = CheckersPiece(Color.WHITE, row, col)
    
    def is_valid_position(self, row: int, col: int) -> bool:
        """Проверить валидность позиции"""
        return 0 <= row < 8 and 0 <= col < 8
    
    def is_empty(self, row: int, col: int) -> bool:
        """Проверить, пуста ли клетка"""
        if not self.is_valid_position(row, col):
            return False
        return self.grid[row][col] is None
    
    def get_piece(self, row: int, col: int) -> Optional[CheckersPiece]:
        """Получить фигуру"""
        if self.is_valid_position(row, col):
            return self.grid[row][col]
        return None
    
    def move_piece(self, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Переместить фигуру"""
        piece = self.get_piece(from_row, from_col)
        if piece is None or not self.is_empty(to_row, to_col):
            return False
        
        captured = None
        
        # Проверить, это не битие
        if abs(to_row - from_row) == 1:
            # Обычный ход
            pass
        elif abs(to_row - from_row) == 2:
            # Битие
            mid_row = (from_row + to_row) // 2
            mid_col = (from_col + to_col) // 2
            captured = self.get_piece(mid_row, mid_col)
            if not captured or captured.color == piece.color:
                return False
            self.grid[mid_row][mid_col] = None
        else:
            return False
        
        # Выполнить ход
        self.grid[to_row][to_col] = piece
        self.grid[from_row][from_col] = None
        piece.row = to_row
        piece.col = to_col
        
        # Проверить превращение в дамку
        # Белые ходят вверх (к строке 0), чёрные ходят вниз (к строке 7)
        if (piece.color == Color.WHITE and to_row == 0) or (piece.color == Color.BLACK and to_row == 7):
            piece.is_king = True
        
        # Сохранить ход
        self.move_history.append(((from_row, from_col), (to_row, to_col), captured))
        
        return True
    
    def undo_move(self) -> bool:
        """Отменить последний ход в шашках"""
        if not self.move_history:
            return False
        
        from_pos, to_pos, captured = self.move_history.pop()
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Получить фигуру, которая была на целевой позиции
        piece = self.get_piece(to_row, to_col)
        if not piece:
            return False
        
        # Вернуть фигуру на исходную позицию
        self.grid[from_row][from_col] = piece
        self.grid[to_row][to_col] = None
        piece.row = from_row
        piece.col = from_col
        
        # Вернуть захваченную фигуру
        if captured:
            mid_row = (from_row + to_row) // 2
            mid_col = (from_col + to_col) // 2
            self.grid[mid_row][mid_col] = captured
        
        # Если фигура была дамкой, но не превратилась в этом ходе, оставляем её дамкой
        # Если она превратилась в этом ходе, нужно вернуть в пешку
        if piece.is_king:
            # Проверяем, была ли это белая фигура, которая достигла верхнего края
            if piece.color == Color.WHITE and to_row == 0 and from_row != 0:
                # Фигура только что превратилась, возвращаем в пешку
                piece.is_king = False
            # Или чёрная фигура, которая достигла нижнего края
            elif piece.color == Color.BLACK and to_row == 7 and from_row != 7:
                # Фигура только что превратилась, возвращаем в пешку
                piece.is_king = False
        
        return True


class CheckersGame:
    """Класс для игры в шашки"""
    def __init__(self, screen=None):
        self.board_size = 800
        self.panel_width = 200
        self.width = self.board_size + self.panel_width
        self.height = 800
        self.square_size = self.board_size // 8
        
        self.screen = screen if screen else pygame.display.set_mode((self.width, self.height))
        if not screen:
            pygame.display.set_caption("Шашки")
        
        self.clock = pygame.time.Clock()
        self.board = CheckersBoard()
        
        # Цвета
        self.light_color = (240, 217, 181)
        self.dark_color = (181, 136, 99)
        self.highlight_color = (186, 202, 43)
        self.white_color = (255, 255, 255)
        self.black_color = (0, 0, 0)
        self.panel_color = (60, 80, 60)
        self.white_player_color = (200, 200, 255)
        self.black_player_color = (255, 150, 150)
        
        # Состояние
        self.current_player = Color.WHITE
        self.selected_position = None
        self.possible_moves = []
        self.running = True
        
        self.font = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        self.menu_button = pygame.Rect(0, 0, 0, 0)
        self.undo_button = pygame.Rect(0, 0, 0, 0)  # Кнопка отката
    
    def handle_click(self, pos: Tuple[int, int]):
        """Обработать клик"""
        # Проверить клик на кнопку отката
        if hasattr(self, 'undo_button') and self.undo_button.collidepoint(pos):
            if self.board.undo_move():
                # Отменили последний ход
                self.current_player = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
                self.selected_position = None
                self.possible_moves = []
            return
        
        # Проверить клик на кнопку меню
        if self.menu_button.collidepoint(pos):
            self.running = False
            return
        
        # Игнорируем клики на панели
        if pos[0] >= self.board_size:
            return
        
        col = pos[0] // self.square_size
        row = pos[1] // self.square_size
        
        if not self.board.is_valid_position(row, col):
            return
        
        # Если клик на возможный ход
        if (row, col) in self.possible_moves:
            # Проверить, это бой?
            distance = abs(row - self.selected_position[0])
            is_capture = distance == 2
            
            self.board.move_piece(self.selected_position[0], self.selected_position[1], row, col)
            
            # Если это был бой, проверяем, может ли фигура продолжить бой
            if is_capture:
                piece = self.board.get_piece(row, col)
                capture_moves = self.get_capture_moves(piece, self.board)
                if capture_moves:
                    # Фигура может продолжить бой - оставляем её выделенной
                    self.selected_position = (row, col)
                    self.possible_moves = capture_moves
                    return
            
            # Ход закончен - переключаемся на следующего игрока
            self.current_player = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
            self.selected_position = None
            self.possible_moves = []
            return
        
        # Выбрать новую фигуру
        piece = self.board.get_piece(row, col)
        if piece and piece.color == self.current_player:
            self.selected_position = (row, col)
            self.possible_moves = piece.get_possible_moves(self.board)
        else:
            self.selected_position = None
            self.possible_moves = []
    
    def get_capture_moves(self, piece: 'CheckersPiece', board: 'CheckersBoard') -> List[Tuple[int, int]]:
        """Получить только ходы с боем для фигуры"""
        moves = []
        capture_directions = [(-2, -2), (-2, 2), (2, -2), (2, 2)]
        
        # Для обычной пешки - только вперёд бить
        if not piece.is_king:
            if piece.color == Color.WHITE:
                capture_directions = [(-2, -2), (-2, 2)]  # Вверх
            else:
                capture_directions = [(2, -2), (2, 2)]  # Вниз
        
        for dr, dc in capture_directions:
            new_row, new_col = piece.row + dr, piece.col + dc
            mid_row, mid_col = piece.row + dr // 2, piece.col + dc // 2
            
            if board.is_valid_position(new_row, new_col) and board.is_empty(new_row, new_col):
                enemy = board.get_piece(mid_row, mid_col)
                if enemy and enemy.color != piece.color:
                    moves.append((new_row, new_col))
        
        return moves
    
    def get_threatened_pieces(self) -> List[Tuple[int, int]]:
        """Получить список позиций фигур текущего игрока, которые под угрозой"""
        threatened = []
        enemy_color = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
        
        # Пройти по всем фигурам врага
        for row in range(8):
            for col in range(8):
                enemy_piece = self.board.get_piece(row, col)
                if enemy_piece and enemy_piece.color == enemy_color:
                    # Получить все возможные ходы этой фигуры врага
                    enemy_moves = enemy_piece.get_possible_moves(self.board)
                    # Добавить все позиции фигур текущего игрока в списке ходов врага
                    for move_pos in enemy_moves:
                        target = self.board.get_piece(move_pos[0], move_pos[1])
                        if target and target.color == self.current_player:
                            threatened.append(move_pos)
        
        return threatened
    
    def draw_board(self):
        """Нарисовать доску"""
        threatened_positions = self.get_threatened_pieces()
        
        for row in range(8):
            for col in range(8):
                rect = pygame.Rect(col * self.square_size, row * self.square_size,
                                 self.square_size, self.square_size)
                
                # Рисуем доску
                if (row + col) % 2 == 0:
                    pygame.draw.rect(self.screen, self.light_color, rect)
                else:
                    pygame.draw.rect(self.screen, self.dark_color, rect)
                
                # Выделить угрожаемые фигуры оранжевым цветом
                if (row, col) in threatened_positions:
                    pygame.draw.rect(self.screen, (255, 165, 0), rect, 3)
                
                # Выделить выбранную фигуру
                if self.selected_position == (row, col):
                    pygame.draw.rect(self.screen, self.highlight_color, rect, 4)
                
                # Выделить возможные ходы
                if (row, col) in self.possible_moves:
                    pygame.draw.rect(self.screen, (0, 200, 0), rect, 3)
    
    def draw_pieces(self):
        """Нарисовать фигуры"""
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece:
                    x = col * self.square_size + self.square_size // 2
                    y = row * self.square_size + self.square_size // 2
                    
                    color = self.white_color if piece.color == Color.WHITE else self.black_color
                    pygame.draw.circle(self.screen, color, (x, y), self.square_size // 3)
                    if piece.is_king:
                        pygame.draw.circle(self.screen, (255, 215, 0), (x, y), self.square_size // 6)
    
    def draw_panel(self):
        """Нарисовать панель"""
        panel_rect = pygame.Rect(self.board_size, 0, self.panel_width, self.height)
        pygame.draw.rect(self.screen, self.panel_color, panel_rect)
        pygame.draw.line(self.screen, (255, 255, 255), 
                        (self.board_size, 0), (self.board_size, self.height), 2)
        
        # Заголовок
        title_font = pygame.font.Font(None, 32)
        title = title_font.render("Шашки", True, (255, 255, 255))
        self.screen.blit(title, (self.board_size + 20, 30))
        
        # Текущий игрок
        y_offset = 100
        small_font = pygame.font.Font(None, 24)
        player_name = "Белые" if self.current_player == Color.WHITE else "Чёрные"
        player_label = small_font.render("Ход:", True, (255, 255, 255))
        self.screen.blit(player_label, (self.board_size + 15, y_offset))
        
        player_box = pygame.Rect(self.board_size + 10, y_offset + 25, self.panel_width - 20, 50)
        if self.current_player == Color.WHITE:
            pygame.draw.rect(self.screen, self.white_player_color, player_box)
            pygame.draw.rect(self.screen, (255, 255, 255), player_box, 3)
        else:
            pygame.draw.rect(self.screen, self.black_player_color, player_box)
            pygame.draw.rect(self.screen, (255, 255, 255), player_box, 3)
        
        player_text = title_font.render(player_name, True, (0, 0, 0))
        player_text_rect = player_text.get_rect(center=player_box.center)
        self.screen.blit(player_text, player_text_rect)
        
        # Кнопка Отката
        y_offset += 100
        self.undo_button = pygame.Rect(self.board_size + 10, y_offset, self.panel_width - 20, 40)
        pygame.draw.rect(self.screen, (100, 150, 200), self.undo_button)
        pygame.draw.rect(self.screen, (255, 255, 255), self.undo_button, 2)
        
        undo_text = small_font.render("Ход назад", True, (255, 255, 255))
        undo_rect = undo_text.get_rect(center=(self.board_size + self.panel_width // 2, y_offset + 20))
        self.screen.blit(undo_text, undo_rect)
        
        # Кнопка Меню
        y_offset += 55
        self.menu_button = pygame.Rect(self.board_size + 10, y_offset, self.panel_width - 20, 50)
        pygame.draw.rect(self.screen, (100, 150, 200), self.menu_button)
        pygame.draw.rect(self.screen, (255, 255, 255), self.menu_button, 2)
        
        menu_text = small_font.render("МЕНЮ", True, (255, 255, 255))
        menu_rect = menu_text.get_rect(center=self.menu_button.center)
        self.screen.blit(menu_text, menu_rect)
    
    def run(self):
        """Главный цикл"""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
            
            self.screen.fill((240, 240, 240))
            self.draw_board()
            self.draw_pieces()
            self.draw_panel()
            
            pygame.display.flip()
            self.clock.tick(60)


if __name__ == "__main__":
    app = GameApplication()
    app.run()
