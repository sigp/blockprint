#!/usr/bin/env fish

set slots_per_period 221184

set num_periods 10

for i in (seq 0 $num_periods)
    set start_slot (math "$i * $slots_per_period + 1")
    set end_slot (math "($i + 1) * $slots_per_period")
    set dir_name "slots_"$start_slot"_to_"$end_slot
    set input_dir "data/mainnet/all/$dir_name"
    set output_dir "data/mainnet/training/$dir_name"
    ./prepare_training_data.py $input_dir $output_dir
end
