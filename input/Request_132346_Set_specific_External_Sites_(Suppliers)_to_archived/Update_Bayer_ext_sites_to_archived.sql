select
	qoq.id ,
	qoq.name__v as "ingnore.current_name",
	'ZZ_DO_NOT_USE_' || qoq.name__v as "name__v",
	qoq.state__v as "ingnore.current_state__v",
	'archived_state__c' as state__v
from
	qms_organization__qdm qoq
left join object_type__v otv on
	otv.id = qoq.object_type__v
where
	lower(qoq.name__v) like '%bayer%'
	and otv.name__v = 'External Site';