update shipment_receipt set tenant_id = 'legacy' where tenant_id is null;
alter table shipment_receipt alter column tenant_id set not null;
