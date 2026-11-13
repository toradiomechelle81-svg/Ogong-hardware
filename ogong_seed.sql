-- ============================================================
-- OGONG BUILDING SUPPLY
-- SAMPLE / SEED DATA
-- MariaDB / MySQL Version
-- ============================================================

USE ogong_db;

-- ============================================================
-- USERS
-- ============================================================

INSERT INTO users
(username, password, full_name, role, status)
VALUES
('admin', 'admin123', 'System Administrator', 'admin', 'active'),
('cashier', 'cashier123', 'Ogong Cashier', 'cashier', 'active'),
('cashier2', 'cashier123', 'Maria Santos', 'cashier', 'active'),
('cashier3', 'cashier123', 'Juan Dela Cruz', 'cashier', 'active'),
('manager', 'manager123', 'Mark Reyes', 'admin', 'active');

-- ============================================================
-- SUPPLIERS
-- ============================================================

INSERT INTO suppliers
(name, contact_person, phone, email, address)
VALUES
('Ogong Building Supply', 'Juan Dela Cruz',
 '09123456789', 'ogong@example.com', 'Cebu City'),

('Cebu Hardware Trading', 'Pedro Santos',
 '09171234567', 'cebuhardware@example.com', 'Mandaue City'),

('Visayas Construction Supply', 'Maria Reyes',
 '09201234567', 'visayasconstruction@example.com', 'Lapu-Lapu City'),

('Philippine Cement Supply', 'Ramon Garcia',
 '09351234567', 'pcs@example.com', 'Cebu City'),

('Power Tools Philippines', 'Carlos Mendoza',
 '09451234567', 'powertools@example.com', 'Mandaue City'),

('Cebu Plumbing Depot', 'Ana Lopez',
 '09551234567', 'plumbing@example.com', 'Cebu City'),

('National Electrical Supply', 'Jose Ramos',
 '09651234567', 'electrical@example.com', 'Talisay City'),

('Steel and Metal Trading', 'Roberto Cruz',
 '09751234567', 'steelmetal@example.com', 'Cebu City'),

('Paint World Cebu', 'Elena Torres',
 '09851234567', 'paintworld@example.com', 'Mandaue City'),

('Builders Choice Supply', 'Michael Tan',
 '09951234567', 'builderschoice@example.com', 'Cebu City');

-- ============================================================
-- CUSTOMERS
-- ============================================================

INSERT INTO customers
(name, phone, email, address)
VALUES
('Juan Dela Cruz', '09111111111',
 'juan@example.com', 'Cebu City'),

('Maria Santos', '09222222222',
 'maria@example.com', 'Talisay City'),

('Pedro Garcia', '09333333333',
 'pedro@example.com', 'Mandaue City'),

('Ana Reyes', '09444444444',
 'ana@example.com', 'Lapu-Lapu City'),

('Carlos Mendoza', '09555555555',
 'carlos@example.com', 'Cebu City'),

('Jose Ramirez', '09666666666',
 'jose@example.com', 'Talisay City'),

('Ramon Cruz', '09777777777',
 'ramon@example.com', 'Cebu City'),

('Elena Torres', '09888888888',
 'elena@example.com', 'Mandaue City'),

('Mark Villanueva', '09999999999',
 'mark@example.com', 'Cebu City'),

('Kevin Reyes', '09123456780',
 'kevin@example.com', 'Lapu-Lapu City');

-- ============================================================
-- PRODUCTS
-- ============================================================

INSERT INTO products
(sku, name, category, unit, price, cost_price, stock, minimum_stock, supplier_id)
VALUES
('HAM-001', 'Claw Hammer', 'Hand Tools', 'Piece',
 350.00, 250.00, 25, 10, 1),

('DRL-001', 'Electric Drill', 'Power Tools', 'Piece',
 2850.00, 2200.00, 8, 10, 5),

('PVC-001', 'PVC Pipe 1/2"', 'Plumbing', 'Meter',
 120.00, 80.00, 50, 15, 6),

('CEM-001', 'Portland Cement', 'Construction Materials', 'Bag',
 285.00, 230.00, 35, 20, 4),

('NAI-001', 'Common Nails 2"', 'Hardware', 'Kilogram',
 95.00, 65.00, 80, 20, 2),

('PNT-001', 'Interior Wall Paint', 'Paint', 'Gallon',
 1250.00, 900.00, 12, 5, 9),

('WIR-001', 'Electrical Wire 2.0mm', 'Electrical', 'Meter',
 45.00, 30.00, 100, 25, 7),

('STL-001', 'Steel Bar 10mm', 'Steel and Metal', 'Piece',
 420.00, 350.00, 40, 10, 8),

('SAW-001', 'Hand Saw 20"', 'Hand Tools', 'Piece',
 550.00, 380.00, 18, 5, 2),

('TAP-001', 'PVC Faucet', 'Plumbing', 'Piece',
 180.00, 120.00, 30, 10, 6),

('SCR-001', 'Wood Screw 1"', 'Hardware', 'Box',
 150.00, 100.00, 45, 10, 2),

('DRL-002', 'Cordless Drill', 'Power Tools', 'Piece',
 3950.00, 3100.00, 7, 5, 5),

('PNT-002', 'Exterior Paint', 'Paint', 'Gallon',
 1450.00, 1050.00, 10, 5, 9),

('CEM-002', 'Rapid Hardening Cement', 'Construction Materials', 'Bag',
 310.00, 250.00, 25, 10, 4),

('WIR-002', 'Electrical Wire 3.5mm', 'Electrical', 'Meter',
 75.00, 52.00, 75, 20, 7);

-- ============================================================
-- SALES
-- ============================================================

INSERT INTO sales
(receipt_no, customer_id, cashier_id, subtotal, discount,
 total, cash_received, change_amount, payment_method)
VALUES
('OR-000001', 1, 2, 700.00, 0.00,
 700.00, 1000.00, 300.00, 'Cash'),

('OR-000002', 2, 2, 2850.00, 100.00,
 2750.00, 3000.00, 250.00, 'Cash'),

('OR-000003', 3, 3, 600.00, 0.00,
 600.00, 600.00, 0.00, 'GCash'),

('OR-000004', 4, 2, 1140.00, 40.00,
 1100.00, 1500.00, 400.00, 'Cash'),

('OR-000005', 5, 3, 1250.00, 0.00,
 1250.00, 1250.00, 0.00, 'GCash'),

('OR-000006', 6, 2, 840.00, 40.00,
 800.00, 1000.00, 200.00, 'Cash'),

('OR-000007', 7, 4, 550.00, 0.00,
 550.00, 600.00, 50.00, 'Cash'),

('OR-000008', 8, 3, 1450.00, 50.00,
 1400.00, 1500.00, 100.00, 'Cash'),

('OR-000009', 9, 2, 900.00, 0.00,
 900.00, 1000.00, 100.00, 'Card'),

('OR-000010', 10, 4, 1260.00, 60.00,
 1200.00, 1500.00, 300.00, 'Cash');

-- ============================================================
-- SALE ITEMS
-- ============================================================

INSERT INTO sale_items
(sale_id, product_id, quantity, price, subtotal)
VALUES
(1, 1, 2, 350.00, 700.00),

(2, 2, 1, 2850.00, 2850.00),

(3, 3, 5, 120.00, 600.00),

(4, 4, 4, 285.00, 1140.00),

(5, 6, 1, 1250.00, 1250.00),

(6, 8, 2, 420.00, 840.00),

(7, 9, 1, 550.00, 550.00),

(8, 13, 1, 1450.00, 1450.00),

(9, 5, 3, 95.00, 285.00),

(9, 7, 10, 45.00, 450.00),

(9, 10, 1, 180.00, 180.00),

(10, 10, 7, 180.00, 1260.00);

-- ============================================================
-- STOCK MOVEMENTS
-- ============================================================

INSERT INTO stock_movements
(product_id, type, quantity, reference, user_id)
VALUES
(1, 'stock_in', 25, 'Initial Stock', 1),

(2, 'stock_in', 10, 'Initial Stock', 1),

(3, 'stock_in', 50, 'Initial Stock', 1),

(4, 'stock_in', 35, 'Initial Stock', 1),

(5, 'stock_in', 80, 'Initial Stock', 1),

(6, 'stock_in', 12, 'Initial Stock', 1),

(7, 'stock_in', 100, 'Initial Stock', 1),

(8, 'stock_in', 40, 'Initial Stock', 1),

(9, 'stock_in', 18, 'Initial Stock', 1),

(10, 'stock_in', 30, 'Initial Stock', 1),

(1, 'stock_out', 2, 'Sale OR-000001', 2),

(2, 'stock_out', 1, 'Sale OR-000002', 2),

(3, 'stock_out', 5, 'Sale OR-000003', 3),

(4, 'stock_out', 4, 'Sale OR-000004', 2),

(6, 'stock_out', 1, 'Sale OR-000005', 3),

(8, 'stock_out', 2, 'Sale OR-000006', 2),

(9, 'stock_out', 1, 'Sale OR-000007', 4),

(5, 'stock_out', 3, 'Sale OR-000009', 2),

(7, 'stock_out', 10, 'Sale OR-000009', 2),

(10, 'stock_out', 8, 'Sale OR-000010', 4);