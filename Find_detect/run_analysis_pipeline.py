import os
import argparse
import sys
from datetime import datetime

# Ensure modules can be imported from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from Find_detect import log_split_bytime
    from Find_detect import COT
except ImportError:
    print("❌ Error: Unable to import 'log_split_bytime' or 'COT'.")
    print("   Please ensure this script is in the same directory as 'log_split_bytime.py' and 'COT.py'.")
    sys.exit(1)

def main():
    """
    Main control script to execute the complete log analysis pipeline:
    1. Split logs by time
    2. Perform COT analysis on logs for specified time period
    """
    parser = argparse.ArgumentParser(description="Complete log analysis pipeline combining log splitting and COT analysis.")
    parser.add_argument('--raw_log_dir', default='./log/log', help="Directory containing raw log files.")
    parser.add_argument('--split_output_dir', default='./split_logs', help="Output directory for time-split logs.")
    parser.add_argument('--final_analysis_dir', default='./Find_detect/analysis_results', help="Output directory for final COT analysis results.")
    parser.add_argument('--target_time', required=True, help="Target time directory name for analysis (format: YYYYMMDD_HHMM).")
    parser.add_argument('--interval_hours', type=int, default=2, help="Time interval for log splitting (hours).")

    args = parser.parse_args()

    # --- Print parameters ---
    print("🚀 Starting log analysis pipeline...")
    print("="*50)
    print(f"Raw log directory:           {args.raw_log_dir}")
    print(f"Split output directory:      {args.split_output_dir}")
    print(f"Final analysis directory:    {args.final_analysis_dir}")
    print(f"Target analysis time:        {args.target_time}")
    print(f"Time splitting interval:     {args.interval_hours} hours")
    print("="*50)

    # --- Step 1: Call log_split_bytime.py for log splitting ---
    print("\n[Step 1/2] Splitting logs by time...")
    try:
        log_split_bytime.split_logs_by_time(
            input_dir=args.raw_log_dir,
            output_dir=args.split_output_dir,
            interval_hours=args.interval_hours
        )
        print("✅ Log splitting completed!")
    except Exception as e:
        print(f"❌ Step 1 failed: Error occurred during log splitting: {e}")
        sys.exit(1)
        
    # --- Step 2: Call COT.py to analyze the specified time folder ---
    print("\n[Step 2/2] Preparing COT analysis for specified time period logs...")

    # Verify target time directory exists
    target_time_dir_for_cot = os.path.join(args.split_output_dir, args.target_time)
    if not os.path.isdir(target_time_dir_for_cot):
        print(f"❌ Error: Target time directory '{target_time_dir_for_cot}' does not exist.")
        print("   Please check if '--target_time' parameter is correct, or if log splitting successfully generated this directory.")
        sys.exit(1)
        
    print(f"   Will analyze directory: {target_time_dir_for_cot}")

    # Create a unique output directory for this analysis
    final_output_path = os.path.join(args.final_analysis_dir, args.target_time)
    os.makedirs(final_output_path, exist_ok=True)
    print(f"   Analysis results will be saved to: {final_output_path}")

    try:
        # Call COT.py main function with correct parameters
        COT.main(
            INPUT_DIR=target_time_dir_for_cot,
            OUTPUT_DIR=final_output_path,
            analyze_log_path=final_output_path
        )
        print("✅ COT analysis completed!")
    except Exception as e:
        import traceback
        print(f"❌ Step 2 failed: Error occurred during COT analysis: {e}")
        print(f"   Detailed error information: {traceback.format_exc()}")
        sys.exit(1)

    print("\n🎉🎉🎉 Pipeline execution completed! 🎉🎉🎉")
    print(f"Final analysis results saved in: {final_output_path}")

if __name__ == "__main__":
    main() 