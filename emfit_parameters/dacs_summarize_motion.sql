select 
r.room_id, h.PID, s.sensor_type, s.sensor_name, s.sensor_id,
d.timestamp,d.local_timestamp,d.sensor_value

from 
livinglab.homes h, livinglab.gateways g, livinglab.rooms r, livinglab.sensors s,
livinglab.sensor_data d
where h.home_id = g.home_id 
      and g.gateway_id=r.gateway_id 
      and h.PID like '%3-%'
      and s.room_id = r.room_id and s.sensor_type like '%Motion%'
      and s.sensor_id = d.sensor_id
