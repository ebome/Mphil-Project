select * from dacs_db.emfit_sleep_data;


alter table dacs_db.emfit_new_sleep_class add column device_id int;
alter table dacs_db.emfit_new_sleep_class drop filename;

/*
# check the data type
desc dacs_db.emfit_sleep_data;
show columns from dacs_db.emfit_sleep_data;
describe dacs_db.emfit_sleep_data;

alter table dacs_db.emfit_sleep_data change column timestamp old_classifier_timestamp varchar(45);
alter table dacs_db.emfit_sleep_data change column activity old_classifier_activity int;

# add-a-column-and-fill-in
alter table dacs_db.emfit_sleep_data add column sensor_udn varchar(6);
update  dacs_db.emfit_sleep_data left join dacs_db.sensors
     on dacs_db.sensors.sensor_id = dacs_db.emfit_sleep_data.device_id
     set dacs_db.emfit_sleep_data.sensor_udn = dacs_db.sensors.sensor_udn
     
     
alter table dacs_db.emfit_sleep_data add column at text;
alter table dacs_db.emfit_sleep_data add column new_classifier_timestamp varchar(45);


update  dacs_db.emfit_sleep_data left join dacs_db.emfit_new_sleep_class
     on dacs_db.emfit_new_sleep_class.sensor_udn = dacs_db.emfit_sleep_data.sensor_udn
     set dacs_db.emfit_sleep_data.at = dacs_db.emfit_new_sleep_class.at
     
*/