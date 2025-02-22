const canvas = document.getElementById('tetris');
const context = canvas.getContext('2d');
const scoreElement = document.getElementById('score');

const ROWS = 20;
const COLS = 10;
const BLOCK_SIZE = 30;
const EMPTY = 0;

let score = 0;
let board = [];
let currentPiece;
let currentX, currentY;

const PIECES = [
    [1, 1, 1, 1], // I
    [[1, 1, 1], [0, 1, 0]], // T
    [[1, 1], [1, 1]], // O
    [[1, 1, 0], [0, 1, 1]], // S
    [[0, 1, 1], [1, 1, 0]], // Z
    [[1, 0, 0], [1, 1, 1]], // L
    [[0, 0, 1], [1, 1, 1]]  // J
];

function createBoard() {
    for (let row = 0; row < ROWS; row++) {
        board[row] = [];
        for (let col = 0; col < COLS; col++) {
            board[row][col] = EMPTY;
        }
    }
}

function drawBlock(x, y, color) {
    context.fillStyle = color;
    context.fillRect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
    context.strokeStyle = '#000';
    context.strokeRect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
}

function drawBoard() {
    for (let row = 0; row < ROWS; row++) {
        for (let col = 0; col < COLS; col++) {
            if (board[row][col] !== EMPTY) {
                drawBlock(col, row, board[row][col]);
            }
        }
    }
}

function drawPiece() {
    currentPiece.shape.forEach((row, y) => {
        row.forEach((value, x) => {
            if (value) {
                drawBlock(currentX + x, currentY + y, currentPiece.color);
            }
        });
    });
}

function draw() {
    context.clearRect(0, 0, canvas.width, canvas.height);
    drawBoard();
    drawPiece();
}

function newPiece() {
    const randomPiece = PIECES[Math.floor(Math.random() * PIECES.length)];
    currentPiece = {
        shape: Array.isArray(randomPiece[0]) ? randomPiece : [randomPiece],
        color: `#${Math.floor(Math.random() * 16777215).toString(16)}`
    };
    currentX = Math.floor(COLS / 2) - Math.floor(currentPiece.shape[0].length / 2);
    currentY = 0;
}

function isValidMove(x, y, piece) {
    return piece.shape.every((row, dy) => {
        return row.every((value, dx) => {
            const newX = x + dx;
            const newY = y + dy;
            return (
                !value ||
                (newX >= 0 && newX < COLS && newY < ROWS && board[newY][newX] === EMPTY)
            );
        });
    });
}

function placePiece() {
    currentPiece.shape.forEach((row, y) => {
        row.forEach((value, x) => {
            if (value) {
                board[currentY + y][currentX + x] = currentPiece.color;
            }
        });
    });
    clearLines();
    newPiece();
    if (!isValidMove(currentX, currentY, currentPiece)) {
        gameOver();
    }
}

function clearLines() {
    let linesCleared = 0;
    for (let row = ROWS - 1; row >= 0; row--) {
        if (board[row].every(cell => cell !== EMPTY)) {
            board.splice(row, 1);
            board.unshift(new Array(COLS).fill(EMPTY));
            linesCleared++;
        }
    }
    if (linesCleared > 0) {
        score += linesCleared * 10;
        scoreElement.textContent = score;
    }
}

function gameOver() {
    alert('游戏结束!');
    board = [];
    createBoard();
    score = 0;
    scoreElement.textContent = score;
}

function drop() {
    if (isValidMove(currentX, currentY + 1, currentPiece)) {
        currentY++;
    } else {
        placePiece();
    }
}

function movePiece(dx) {
    if (isValidMove(currentX + dx, currentY, currentPiece)) {
        currentX += dx;
    }
}

function rotatePiece() {
    const rotated = currentPiece.shape[0].map((_, i) =>
        currentPiece.shape.map(row => row[i]).reverse()
    );
    if (isValidMove(currentX, currentY, { shape: rotated, color: currentPiece.color })) {
        currentPiece.shape = rotated;
    }
}

document.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft') {
        movePiece(-1);
    } else if (event.key === 'ArrowRight') {
        movePiece(1);
    } else if (event.key === 'ArrowDown') {
        drop();
    } else if (event.key === 'ArrowUp') {
        rotatePiece();
    }
    draw();
});

function gameLoop() {
    drop();
    draw();
    setTimeout(gameLoop, 1000);
}

createBoard();
newPiece();
gameLoop();