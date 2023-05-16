add_one(){
    time_offset=$1
    time_scale=$2
    file_offset=$3
    selection=$(( $RANDOM % 1000 ))
    head -n20000 all.patterns | grep -v '^-1' |\
        awk -v selection=$selection -v time_scale=$time_scale -v time_offset=$time_offset -v file_offset=$file_offset \
        'BEGIN{count=0} /^$/{count++; next} count==selection{$1=$1*time_scale + time_offset; $3=$3+file_offset; $4=$4+file_offset; $5=$5+file_offset; $6=$6+file_offset; print}'
}

augment(){
    add_one 0 1 0 > /tmp/augment_out
    for i in $(seq 1 $1)
    do
        time_offset=$(( $(cat /tmp/augment_out | cut -d' ' -f1 | sort -g | tail -n1) + 1 ))
        for j in $(seq 1 $2)
        do
            time_scale=$(( $RANDOM % 5 ))
            file_offset=$(( $j * 10 + 1 ))
            add_one $time_offset $time_scale $file_offset >> /tmp/augment_out
        done
    done
    cat /tmp/augment_out | sort -g
}

