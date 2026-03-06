-- Mock data for schema: parse_session, product, price_history
--
-- Usage:
--   docker compose exec -T db psql -U results_user -d results_db < sql/mock_data.sql

BEGIN;

-- For repeatable local tests
TRUNCATE TABLE price_history, product, parse_session, site, "user" RESTART IDENTITY CASCADE;

INSERT INTO site (id, name, base_url, created_at)
VALUES
    (1, 'Market A', 'https://market-a.local', NOW()),
    (2, 'Market B', 'https://market-b.local', NOW());

INSERT INTO "user" (id, username, created_at)
VALUES
    (1, 'admin', NOW()),
    (2, 'analyst', NOW());

INSERT INTO parse_session (
    id,
    site_id,
    user_id,
    status,
    started_at,
    ended_at,
    processed_items
)
VALUES
    (1, 1, 1, 'completed', '2026-03-06 10:00:00+00', '2026-03-06 10:15:00+00', 120),
    (2, 1, 2, 'in_progress', '2026-03-06 12:00:00+00', NULL, 45),
    (3, 2, 1, 'completed', '2026-03-06 09:30:00+00', '2026-03-06 09:42:00+00', 78);

INSERT INTO product (
    id,
    site_id,
    external_id,
    name,
    price,
    old_price,
    currency,
    description,
    category,
    in_stock,
    updated_at
)
VALUES
    (
        1,
        1,
        'A-1001',
        'Молоко 900 мл',
        119.90,
        129.90,
        'RUB',
        'Пастеризованное молоко 3.2%',
        'Молочные продукты',
        TRUE,
        '2026-03-06 10:16:00+00'
    ),
    (
        2,
        1,
        'A-1002',
        'Кефир 1 л',
        99.00,
        104.00,
        'RUB',
        'Кефир 2.5%',
        'Молочные продукты',
        TRUE,
        '2026-03-06 10:16:30+00'
    ),
    (
        3,
        1,
        'A-1003',
        'Сыр Гауда 300 г',
        259.00,
        NULL,
        'RUB',
        'Твердый сыр, нарезка',
        'Сыры',
        FALSE,
        '2026-03-06 10:17:00+00'
    ),
    (
        4,
        2,
        'B-2001',
        'Корм для кошек 85 г',
        42.00,
        45.00,
        'RUB',
        'Влажный корм, курица',
        'Зоотовары',
        TRUE,
        '2026-03-06 09:43:00+00'
    ),
    (
        5,
        2,
        'B-2002',
        'Наушники Bluetooth',
        2890.00,
        3190.00,
        'RUB',
        'Беспроводные наушники с микрофоном',
        'Электроника',
        TRUE,
        '2026-03-06 09:44:00+00'
    ),
    (
        6,
        2,
        'B-2003',
        'Клавиатура механическая',
        4990.00,
        NULL,
        'RUB',
        'Механические переключатели red',
        'Электроника',
        FALSE,
        '2026-03-06 09:44:30+00'
    );

INSERT INTO price_history (
    id,
    product_id,
    price,
    changed_at
)
VALUES
    (1, 1, 139.90, '2026-03-04 08:00:00+00'),
    (2, 1, 129.90, '2026-03-05 08:00:00+00'),
    (3, 1, 119.90, '2026-03-06 10:16:00+00'),

    (4, 2, 109.00, '2026-03-05 07:30:00+00'),
    (5, 2, 104.00, '2026-03-05 18:00:00+00'),
    (6, 2, 99.00, '2026-03-06 10:16:30+00'),

    (7, 4, 49.00, '2026-03-04 06:00:00+00'),
    (8, 4, 45.00, '2026-03-05 06:00:00+00'),
    (9, 4, 42.00, '2026-03-06 09:43:00+00'),

    (10, 5, 3290.00, '2026-03-04 12:00:00+00'),
    (11, 5, 3190.00, '2026-03-05 12:00:00+00'),
    (12, 5, 2890.00, '2026-03-06 09:44:00+00');

COMMIT;
