#!/usr/bin/env fish

set slots_per_period 221184

set num_periods 10

for i in (seq 1 $num_periods)
    set start_slot (math "$i * $slots_per_period + 1")
    set end_slot (math "($i + 1) * $slots_per_period")
    set output_dir "data/mainnet/all/slots_"$start_slot"_to_"$end_slot
    echo "loading period from $start_slot to $end_slot"
    ./load_blocks.py $start_slot $end_slot $output_dir
end
