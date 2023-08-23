with

posthog as (
  select
    uuid as event_id,
    distinct_id,
    json_extract_scalar(properties,"$['device_id']") as device_id,
    json_extract_scalar(properties,"$['uuid']") as user_uuid,
    json_extract_scalar(properties,"$['ip']") as ip,
  from posthog__events
),

event_ids as (
  select event_id, distinct_id as id from posthog where distinct_id is not null
  union all
  select event_id, user_uuid as id from posthog where user_uuid is not null
  union all
  select event_id, device_id as id from posthog where device_id is not null
),

event_id_groups as ( --event level ids group (distinct_id, device_id and user_id/uuid) used for mapping it with user level ids group
  select
    event_id,
    to_json_string(array_agg(distinct id order by id)) as event_ids_group
  from event_ids
  group by 1
),

event_id_groups_flat as (
  select
    event_ids_group,
    id
  from event_id_groups, unnest(json_extract_string_array(event_ids_group)) as id
  group by 1, 2
  order by 1
),

ids_join as (
  select distinct
    event_id_groups_flat.*,
    ph1.user_uuid as id2,
    ph1.device_id as id3,
    ph2.distinct_id as id4,
    ph2.device_id as id5,
    ph3.user_uuid as id6,
    ph3.distinct_id as id7
  from event_id_groups_flat
  left join posthog ph1
    on ph1.distinct_id = event_id_groups_flat.id
  left join posthog ph2
    on ph2.user_uuid = event_id_groups_flat.id
  left join posthog ph3
    on ph3.device_id = event_id_groups_flat.id
),

event_group_ids as (
  select * 
  from (
    select event_ids_group, id from ids_join
    union all
    select event_ids_group, id2 from ids_join
    union all
    select event_ids_group, id3 from ids_join
    union all
    select event_ids_group, id4 from ids_join
    union all
    select event_ids_group, id5 from ids_join
    union all
    select event_ids_group, id6 from ids_join
    union all
    select event_ids_group, id7 from ids_join
  ) 
  where id is not null
  group by 1, 2
),

final as (
  select
    event_ids_group,
    to_json_string(array_agg(distinct id order by id)) as user_ids_json,
    array_agg(id) as user_ids
  from event_group_ids  
  group by 1
)

select * from final
