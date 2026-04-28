# Delete specific PLAXIS phases from open server
from plxscripting.easy import *

try:
    # Connect to PLAXIS
    LOCALHOST_PORT = 10000
    PASSWORD = 'test123'
    
    print("Connecting to PLAXIS server...")
    s_i, g_i = new_server('localhost', LOCALHOST_PORT, password=PASSWORD)
    print("✓ Connected to PLAXIS\n")
    
    # Get all phases
    phases_list = list(g_i.phases)
    print(f"Total phases before deletion: {len(phases_list)}\n")
    
    # Phases to delete
    phases_to_delete = [
        "GHOST_NoLoad", "COMPARISON_NoLoad",
        "GHOST_FullLoad", "COMPARISON_FullLoad",
        "GHOST_80Load", "COMPARISON_80Load",
        "GHOST_ThirdLoad", "COMPARISON_ThirdLoad"
    ]
    
    # Also delete all Day_* phases and Evt_* phases (cyclic loading events)
    deleted_count = 0
    print("Deleting phases...")
    print("-" * 80)
    
    # Need to refresh list and delete from end to avoid index issues
    for phase in reversed(list(g_i.phases)):
        phase_name = str(phase.Name)
        
        # Check if should be deleted
        if phase_name in phases_to_delete or phase_name.startswith("Event_") or phase_name.startswith("Day_") or "[Evt_" in phase_name:
            try:
                g_i.delete(phase)
                print(f"✓ Deleted: {phase_name}")
                deleted_count += 1
            except Exception as e:
                print(f"✗ Failed to delete {phase_name}: {str(e)}")
    
    print("-" * 80)
    print(f"\nDeleted {deleted_count} phases")
    
    # Show remaining phases
    phases_list_after = list(g_i.phases)
    print(f"Total phases after deletion: {len(phases_list_after)}\n")
    print("Remaining phases:")
    for idx, phase in enumerate(phases_list_after, 1):
        print(f"  {idx}. {phase.Name}")

except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
