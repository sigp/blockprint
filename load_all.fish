#!/usr/bin/env fish

set slots_per_period 221184
set num_periods 1
set offset 2375680

for i in (seq 0 $num_periods)
    set start_slot (math "$offset + $i * $slots_per_period + 1")
    set end_slot (math "$offset + ($i + 1) * $slots_per_period")
    set output_dir "data/mainnet/all/slots_"$start_slot"_to_"$end_slot
    echo "loading period from $start_slot to $end_slot"
    ./load_blocks.py $start_slot $end_slot $output_dir
end
