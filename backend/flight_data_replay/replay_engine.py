"""
    Replay System for pre and post flight data analysis
    This function when ran will send packets in a live manner to the websocket mainly for real time pre/post flight analysis.
    Aim of this replay system is to standardise data as well as remove any excess functions no longer needed in this GCS
"""
import csv
import time
import pandas as pd
from datetime import datetime as dt
from enum import Enum, auto



# ======================
# Configuration Settings
# ======================
# Enums for differentiaiting the two data source types
class DataSource(Enum):
    MISSION = auto()
    SIM = auto()


# Make sure to add the additional section for mission_data or simulation_data
DEFAULT_ROUTE = "GCS/backend/flight_data_replay/data"
PACKET_TIMEOUT = 100 # in ms

# ==================
# Main Replay System
# ==================
class ReplaySystem:
    def __init__(self, data_source, file_path, window_size=PACKET_TIMEOUT):
        self.data_source = data_source
        self.file_path = file_path
        self.window_size = window_size
        self.df = None
        self.processed_windows = []
        
    def run_engine(self):
        """ Running the engine """
        # There will be temp print functions for testing reasons
        print(f"Executing replay engine in {self.data_source.name} mode")
        
        self.load_data()
        self.preprocess_data()
        self.get_apogee()
        self.add_state_transitions()
        self.process_windows()
        self.replay_data()
        
    # ====================
    # Data Loading Methods
    # ====================
    def load_data(self):
        """ Load data based on the user selected source
            Currently available as mission_data or simulation_data
        """
        try:
            self.df = pd.read_csv(self.file_path)
            
            
                
        except Exception as e:
            raise RuntimeError(f"Error found loading {self.data_source.name} data with: {e}")
        
    