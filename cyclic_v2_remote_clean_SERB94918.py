# PLAXIS 2D Cyclic Loading - Using Remote Scripting Server
# IMPORTANT: PLAXIS must already be open with Remote Scripting Server enabled!

from plxscripting.easy import *
import random
import json
import sys
from datetime import datetime

output_file = r"C:\Users\SERB94918\cyclic_output_final.txt"
log = open(output_file, "w", encoding="utf-8")

def write_log(text):
    print(text)
    log.write(text + "\n")
    log.flush()
 
try:
    # Load configuration
    config_file = r"C:\Users\SERB94918\WSP O365\Sandberg, Arvid - EXJOBB\VS\schedules.json"
    
    # Get number of tracks from command line
    if len(sys.argv) < 2:
        print("Usage: python cyclic_v2_remote_clean.py <num_tracks>")
        raise Exception("Number of tracks must be specified as command-line argument")
    
    try:
        NUM_TRACKS = int(sys.argv[1])
    except ValueError:
        raise Exception(f"Invalid track count: {sys.argv[1]}. Must be an integer.")
    
    write_log(f"Loading configuration for {NUM_TRACKS} tracks...")
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    write_log(f"✓ Configuration loaded")
    
    # PLAXIS connection settings
    LOCALHOST_PORT = 10000
    PASSWORD = 'test123'
    
    # Extract configuration
    SCHEDULE_DURATION = config['simulation']['total_duration_days']
    TRAIN_DURATION = config['simulation']['train_duration_hours'] / 24
    DAILY_SCHEDULE = config['daily_schedule']
    LOAD_VALUE = config['simulation']['load_kpa']
    
    # Connect to PLAXIS
    try:
        s_i, g_i = new_server('localhost', LOCALHOST_PORT, password=PASSWORD)
        write_log("✓ Connected to PLAXIS")
    except Exception as e:
        write_log(f"ERROR: Connection failed: {str(e)}")
        raise
    
    # Get phases and loads
    phases_list = list(g_i.phases)
    if not phases_list:
        raise Exception("No phases found in model")
    
    write_log(f"✓ Found {len(phases_list)} phases")
    
    # Detect available loads dynamically
    loads = []
    load_idx = 1
    while True:
        try:
            load = getattr(g_i, f"LineLoad_{load_idx}_1")
            loads.append(load)
            load_idx += 1
        except:
            break
    
    if not loads:
        raise Exception("No loads found in model")
    
    write_log(f"✓ Found {len(loads)} loads")
    
    # Find starting phase (ES2C or last phase)
    embankment_consolidation_phase = None
    for p in phases_list:
        phase_name = str(p.Name)
        if "ES2C" in phase_name or phase_name == "Phase_8":
            embankment_consolidation_phase = p
            break
    
    if not embankment_consolidation_phase:
        embankment_consolidation_phase = phases_list[-1]
    
    last_phase = embankment_consolidation_phase
    total_schedule_time = SCHEDULE_DURATION
    
    write_log(f"✓ Starting from phase: {embankment_consolidation_phase.Name}")
    
    # Create comparison phases
    write_log("\nCreating comparison phases...")
    
    # Ghost phase for No Load
    ghost_no_load = g_i.phase(embankment_consolidation_phase)
    ghost_no_load.Name = "GHOST_NoLoad"
    ghost_no_load.DeformCalcType = "Consolidation"
    ghost_no_load.TimeInterval = 1  # 1 day duration
    ghost_no_load.PreviousPhase = embankment_consolidation_phase
    
    for feature in ghost_no_load.UserFeatures:
        if feature.TypeName == "Deform":
            feature.ForceFullyDrainedOnActivation = False
            break
    
    try:
        ghost_no_load.Deform.UseDefaultIterationParams = False
        ghost_no_load.Deform.MaxLoadFractionPerStep = 0.01
    except:
        pass
    
    for load in loads:
        load.deactivate(ghost_no_load)
    
    write_log("✓ GHOST_NoLoad created")
    
    # No Load phase
    phase_no_load = g_i.phase(embankment_consolidation_phase)
    phase_no_load.Name = "COMPARISON_NoLoad"
    phase_no_load.DeformCalcType = "Consolidation"
    phase_no_load.TimeInterval = total_schedule_time
    phase_no_load.PreviousPhase = ghost_no_load
    
    for feature in phase_no_load.UserFeatures:
        if feature.TypeName == "Deform":
            feature.ForceFullyDrainedOnActivation = False
            break
    
    try:
        phase_no_load.Deform.UseDefaultIterationParams = False
        phase_no_load.Deform.MaxLoadFractionPerStep = 0.01
    except:
        pass
    
    for load in loads:
        load.deactivate(phase_no_load)
    
    write_log("✓ COMPARISON_NoLoad created")
    
    # Ghost phase for Full Load
    ghost_full_load = g_i.phase(embankment_consolidation_phase)
    ghost_full_load.Name = "GHOST_FullLoad"
    ghost_full_load.DeformCalcType = "Consolidation"
    ghost_full_load.TimeInterval = 1  # 1 day duration
    ghost_full_load.PreviousPhase = embankment_consolidation_phase
    
    for feature in ghost_full_load.UserFeatures:
        if feature.TypeName == "Deform":
            feature.ForceFullyDrainedOnActivation = False
            break
    
    try:
        ghost_full_load.Deform.UseDefaultIterationParams = False
        ghost_full_load.Deform.MaxLoadFractionPerStep = 0.01
    except:
        pass
    
    for load in loads:
        load.activate(ghost_full_load)
    
    try:
        full_load_value = -LOAD_VALUE
        for load in loads:
            load.qy_start[ghost_full_load] = full_load_value
    except:
        pass
    
    write_log("✓ GHOST_FullLoad created")
    
    # Full Load phase
    phase_full_load = g_i.phase(embankment_consolidation_phase)
    phase_full_load.Name = "COMPARISON_FullLoad"
    phase_full_load.DeformCalcType = "Consolidation"
    phase_full_load.TimeInterval = total_schedule_time
    phase_full_load.PreviousPhase = ghost_full_load
    
    for feature in phase_full_load.UserFeatures:
        if feature.TypeName == "Deform":
            feature.ForceFullyDrainedOnActivation = False
            break
    
    try:
        phase_full_load.Deform.UseDefaultIterationParams = False
        phase_full_load.Deform.MaxLoadFractionPerStep = 0.01
    except:
        pass
    
    for load in loads:
        load.activate(phase_full_load)
    
    try:
        full_load_value = -LOAD_VALUE
        for load in loads:
            load.qy_start[phase_full_load] = full_load_value
    except:
        pass
    
    write_log("✓ COMPARISON_FullLoad created")
    
    # Ghost phase for 80% Load
    ghost_third_load = g_i.phase(embankment_consolidation_phase)
    ghost_third_load.Name = "GHOST_80Load"
    ghost_third_load.DeformCalcType = "Consolidation"
    ghost_third_load.TimeInterval = 1  # 1 day duration
    ghost_third_load.PreviousPhase = embankment_consolidation_phase
    
    for feature in ghost_third_load.UserFeatures:
        if feature.TypeName == "Deform":
            feature.ForceFullyDrainedOnActivation = False
            break
    
    try:
        ghost_third_load.Deform.UseDefaultIterationParams = False
        ghost_third_load.Deform.MaxLoadFractionPerStep = 0.01
    except:
        pass
    
    for load in loads:
        load.activate(ghost_third_load)
    
    try:
        third_load_value = -LOAD_VALUE * 0.8
        for load in loads:
            load.qy_start[ghost_third_load] = third_load_value
    except:
        pass
    
    write_log("✓ GHOST_80Load created")
    
    # 80% Load phase
    phase_third_load = g_i.phase(embankment_consolidation_phase)
    phase_third_load.Name = "COMPARISON_80Load"
    phase_third_load.DeformCalcType = "Consolidation"
    phase_third_load.TimeInterval = total_schedule_time
    phase_third_load.PreviousPhase = ghost_third_load
    
    for feature in phase_third_load.UserFeatures:
        if feature.TypeName == "Deform":
            feature.ForceFullyDrainedOnActivation = False
            break
    
    try:
        phase_third_load.Deform.UseDefaultIterationParams = False
        phase_third_load.Deform.MaxLoadFractionPerStep = 0.01
    except:
        pass
    
    for load in loads:
        load.activate(phase_third_load)
    
    try:
        third_load_value = -LOAD_VALUE * 0.8
        for load in loads:
            load.qy_start[phase_third_load] = third_load_value
    except:
        pass
    
    write_log("✓ COMPARISON_80Load created")
    
    # Generate schedule based on occupancy rates
    write_log(f"\nGenerating schedule ({SCHEDULE_DURATION} days, {NUM_TRACKS} tracks)...")
    
    schedule = []
    current_day = 0
    event_count = 0
    
    while current_day < SCHEDULE_DURATION:
        for period in DAILY_SCHEDULE:
            occupancy = period['occupancy_rate']
            period_hours = period['hours_end'] - period['hours_start']
            period_days = period_hours / 24
            
            occupied_time_in_period = period_days * occupancy
            trains_in_period = int(occupied_time_in_period / TRAIN_DURATION + 0.5)
            
            if trains_in_period == 0:
                trains_in_period = 1 if occupancy > 0.15 else 0
            
            period_start_day = current_day + (period['hours_start'] / 24)
            gap_between_trains = period_days / max(trains_in_period, 1)
            
            for train_idx in range(trains_in_period):
                train_start = period_start_day + (train_idx * gap_between_trains)
                
                if train_start + TRAIN_DURATION <= current_day + 1:
                    # Calculate occupied tracks with smart rounding
                    if occupancy < 0.4:
                        occupied_tracks = int(NUM_TRACKS * occupancy)  # Round DOWN for low occupancy
                    else:
                        occupied_tracks = int(NUM_TRACKS * occupancy + 0.9)  # Round UP for high occupancy
                    occupied_tracks = max(1, occupied_tracks)
                    
                    schedule.append({
                        "type": "train",
                        "load_kpa": LOAD_VALUE,
                        "start": train_start,
                        "duration": TRAIN_DURATION,
                        "end": train_start + TRAIN_DURATION,
                        "occupancy": occupancy,
                        "occupied_tracks": occupied_tracks
                    })
                    event_count += 1
        
        current_day += 1
    
    write_log(f"✓ Generated {len(schedule)} schedule events")
    
    # Create phases from schedule
    write_log(f"\nCreating {len(schedule)} cyclic phases...")
    
    phases_created = 0
    for idx, event in enumerate(schedule, 1):
        try:
            phase = g_i.phase(last_phase)
            occupied_tracks = event['occupied_tracks']
            day_number = int(event['start']) + 1
            phase.Name = f"Day_{day_number}_Event_{idx}"
            phase.DeformCalcType = "Consolidation"
            phase.TimeInterval = event['duration']
            
            for feature in phase.UserFeatures:
                if feature.TypeName == "Deform":
                    feature.ForceFullyDrainedOnActivation = False
                    break
            
            # Randomly select which loads to activate
            loads_to_activate = random.sample(range(len(loads)), occupied_tracks)
            loads_to_activate.sort()
            
            for i, load in enumerate(loads):
                if i in loads_to_activate:
                    load.activate(phase)
                else:
                    load.deactivate(phase)
            
            last_phase = phase
            phases_created += 1
            
            if idx % 50 == 0:
                write_log(f"  Created {phases_created} phases...")
        
        except Exception as e:
            write_log(f"ERROR creating phase {idx}: {str(e)}")
            break
    
    write_log(f"\n✓ SUCCESS: {phases_created} cyclic phases created!")

except Exception as e:
    write_log(f"\nERROR: {str(e)}")
    import traceback
    write_log(traceback.format_exc())

finally:
    write_log("\n[Complete]")
    log.close()
