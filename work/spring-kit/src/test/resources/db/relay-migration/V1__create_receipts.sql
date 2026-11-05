create table shipment_receipt (
    receipt_id bigint primary key,
    amount_minor integer not null
);
insert into shipment_receipt(receipt_id, amount_minor) values (101, 700);
