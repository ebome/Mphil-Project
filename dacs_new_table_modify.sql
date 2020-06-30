-- select count(*) from dacs_db.sensors where sensor_name like "%Bed Sensor%"; /*105 rows*/
-- select * from dacs_db.sensors where sensor_name like "%bed sensor%"; /*sensor_udn will be seen. They contain 6 digits*/


# Add the sensor_udn to new_sleep_summary table
alter table dacs_db.dacs_new_sleep_summary add column sensor_udn varchar(6);
update dacs_db.dacs_new_sleep_summary set sensor_udn=substr(filename,1,6) ;

update dacs_db.dacs_new_sleep_summary left join dacs_db.emfit_summary_data 
     on dacs_db.emfit_summary_data.sensor_udn = dacs_db.dacs_new_sleep_summary.sensor_udn
     and dacs_db.emfit_summary_data.start_time = dacs_db.dacs_new_sleep_summary.from
     set 
     -- dacs_db.dacs_new_sleep_summary.avg_hr = dacs_db.emfit_summary_data.average_heart_rate
	 -- dacs_db.dacs_new_sleep_summary.avg_rr = dacs_db.emfit_summary_data.average_respiration_rate
     -- dacs_db.dacs_new_sleep_summary.avg_act = dacs_db.emfit_summary_data.average_physical_activity    
     -- dacs_db.dacs_new_sleep_summary.tossnturn_count = dacs_db.emfit_summary_data.toss_turn_count
     -- dacs_db.dacs_new_sleep_summary.bedexit_count = dacs_db.emfit_summary_data.bed_exit_count
     
	 -- dacs_db.dacs_new_sleep_summary.hr_min = dacs_db.emfit_summary_data.min_heart_rate
     -- dacs_db.dacs_new_sleep_summary.hr_max = dacs_db.emfit_summary_data.max_heart_rate
     -- dacs_db.dacs_new_sleep_summary.rr_min = dacs_db.emfit_summary_data.min_respiration_rate
     -- dacs_db.dacs_new_sleep_summary.rr_max = dacs_db.emfit_summary_data.max_respiration_rate
     -- dacs_db.dacs_new_sleep_summary.hrv_rmssd_evening = dacs_db.emfit_summary_data.hrv_rmssd_evening
     -- dacs_db.dacs_new_sleep_summary.hrv_rmssd_morning = dacs_db.emfit_summary_data.hrv_rmssd_morning
     -- dacs_db.dacs_new_sleep_summary.hrv_lf = dacs_db.emfit_summary_data.hrv_lf
     -- dacs_db.dacs_new_sleep_summary.hrv_hf = dacs_db.emfit_summary_data.hrv_hf
      dacs_db.dacs_new_sleep_summary.hrv_score = dacs_db.emfit_summary_data.hrv_score

