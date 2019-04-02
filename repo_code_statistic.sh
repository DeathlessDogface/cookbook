#!/usr/bin/env bash
# run the scripts and get the code_num.txt
# copy code_num.txt content to windows Word.doc file
# get form by spliting lines with ","
# copy the form to windows Excel.xls file

root_dir=$(pwd)
echo "working in ${root_dir}"
echo project,name,added lines,removed lines,total lines > ${root_dir}/code_num.txt
for project in $(cat .repo/project.list);do
	cd ${root_dir}/${project}
	pwd
	git log  --format='%aN' | sort -u | while read name; do echo -en "$project,$name"; git log --author="$name" --pretty=tformat:  --since ==2018-9-1 --numstat | awk '{ add += $1; subs += $2; loc += $1 - $2 } END { printf ",%s,%s,%s\n", add, subs, loc }' -; done>> ${root_dir}/code_num.txt
done
