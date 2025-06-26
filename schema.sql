-- Tabla de Materiales
CREATE TABLE IF NOT EXISTS Materiales (
    id_material INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    unidad_medida TEXT NOT NULL,
    stock_actual REAL NOT NULL DEFAULT 0,
    stock_minimo REAL DEFAULT 0,
    fecha_movimiento TEXT DEFAULT (datetime('now', 'localtime')),
    activo INTEGER DEFAULT 1
);

-- Tabla de Movimientos
CREATE TABLE IF NOT EXISTS Movimientos (
    id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,
    id_material INTEGER NOT NULL,
    tipo_movimiento TEXT CHECK(tipo_movimiento IN ('entrada', 'salida')) NOT NULL,
    cantidad REAL NOT NULL,
    fecha_movimiento TEXT DEFAULT (datetime('now', 'localtime')),
    responsable TEXT NOT NULL,
    proyecto_destino TEXT,
    observaciones TEXT,
    FOREIGN KEY (id_material) REFERENCES Materiales(id_material)
);

-- Vistas
CREATE VIEW IF NOT EXISTS VistaStock AS
SELECT 
    m.id_material, 
    m.codigo, 
    m.nombre, 
    m.descripcion, 
    m.unidad_medida, 
    m.stock_actual, 
    m.stock_minimo,
    CASE WHEN m.stock_actual <= m.stock_minimo THEN 'REORDEN' ELSE 'OK' END AS estado
FROM Materiales m

WHERE m.activo = 1
AND m.stock_actual > 0;

CREATE VIEW IF NOT EXISTS VistaHistorial AS
SELECT 
    mov.id_movimiento,
    mat.codigo,
    mat.nombre AS material,
    mov.tipo_movimiento,
    mov.cantidad,
    mat.unidad_medida,
    mov.fecha_movimiento,
    mov.responsable,
    mov.proyecto_destino,
    mov.observaciones
FROM Movimientos mov
JOIN Materiales mat ON mov.id_material = mat.id_material
ORDER BY mov.fecha_movimiento DESC;

-- Triggers para actualización automática de stock
CREATE TRIGGER IF NOT EXISTS actualizar_stock_entrada
AFTER INSERT ON Movimientos
WHEN NEW.tipo_movimiento = 'entrada'
BEGIN
    UPDATE Materiales 
    SET stock_actual = stock_actual + NEW.cantidad
    WHERE id_material = NEW.id_material;
END;

CREATE TRIGGER IF NOT EXISTS actualizar_stock_salida
AFTER INSERT ON Movimientos
WHEN NEW.tipo_movimiento = 'salida'
BEGIN
    UPDATE Materiales 
    SET stock_actual = stock_actual - NEW.cantidad
    WHERE id_material = NEW.id_material;
END;