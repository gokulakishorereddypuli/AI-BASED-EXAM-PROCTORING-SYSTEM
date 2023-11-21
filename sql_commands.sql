truncate table students.stu_data;

insert into students.stu_data values('812201','Mercer J','Donovan J','Kara J');


create table students.stu_data(
`rollno` varchar(30),
`sname` varchar(30),
`fname` varchar(30),
`mname` varchar(30)
);



delete from students.stu_details where rollno=812202;
select * from students.stu_details;
insert into students.stu_details values('812202','100703');

truncate table students.quiz_results;

ALTER TABLE students.quiz_results
MODIFY COLUMN marks VARCHAR(20);

select * from students.quiz_results;
create table students.quiz_results(
`rollno` varchar(20),
`marks` int
);