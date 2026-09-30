INSERT INTO modality(id,name,description,ip,port,timeout)
VALUES(1,'DCM4CHEE','Local hospital archive','dcm4chee5',2575,10000)
ON CONFLICT(id) DO UPDATE SET ip=EXCLUDED.ip,port=EXCLUDED.port;
INSERT INTO order_type(id,name,modality_id)
VALUES(1,'Radiology Order',1)
ON CONFLICT(id) DO UPDATE SET modality_id=EXCLUDED.modality_id;
