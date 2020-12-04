SELECT 
h.PID,s.room_id,s.sensor_id, s.sensor_type,s.sensor_udn,s.sensor_name,
d.*

FROM 
livinglab.sensors s, livinglab.homes h, livinglab.gateways g, 
livinglab.emfit_summary_data d

where s.sensor_type like '%sleep%'
      and h.home_id = g.home_id
      and h.PID like '%3-%'
      and g.gateway_id = s.gateway_id
      
      and s.sensor_id = d.device_id
