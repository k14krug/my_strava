"""Power metrics calculation utilities."""


class PowerCalculator:
    """Handles power-related calculations."""
    
    @staticmethod
    def calculate_power_intervals(stream_data):
        """
        Calculate best power intervals from stream data.
        
        Args:
            stream_data: Dictionary containing 'watts' and 'time' arrays
            
        Returns:
            dict: Power metrics dictionary
        """
        if not stream_data or not isinstance(stream_data, dict):
            print("⚠️ Invalid stream data format")
            return None
            
        if 'watts' not in stream_data or 'time' not in stream_data:
            print("⚠️ Missing required power or time data")
            return None
            
        try:
            power_data = stream_data['watts']
            time_data = stream_data['time']
            
            # Validate data quality
            print(f"Power data points: {len(power_data)}")
            
            # Validate data consistency
            if len(power_data) != len(time_data):
                print("⚠️ Power and time data length mismatch")
                return None
                
            # Remove any None or invalid power values
            valid_data = [(p, t) for p, t in zip(power_data, time_data) if isinstance(p, (int, float)) and p >= 0]
            if not valid_data:
                print("⚠️ No valid power data found")
                return None
                
            power_data, time_data = zip(*valid_data)
            
            # Calculate best power intervals
            intervals = {}
            
            # Calculate minute-based intervals (10, 20, 30, 45 minutes)
            # 10 minutes = 600 seconds
            if len(power_data) >= 600:
                try:
                    intervals['10m'] = max(PowerCalculator.rolling_average(power_data, time_data, 600))
                except (ValueError, IndexError):
                    print("⚠️ Insufficient data for 10m power calculation")
                    intervals['10m'] = 0
            else:
                print(f"⚠️ Activity too short for 10m power calculation ({len(power_data)} data points)")
                intervals['10m'] = 0
                
            # 20 minutes = 1200 seconds
            if len(power_data) >= 1200:
                try:
                    intervals['20m'] = max(PowerCalculator.rolling_average(power_data, time_data, 1200))
                except (ValueError, IndexError):
                    print("⚠️ Insufficient data for 20m power calculation")
                    intervals['20m'] = 0
            else:
                print(f"⚠️ Activity too short for 20m power calculation ({len(power_data)} data points)")
                intervals['20m'] = 0
                
            # 30 minutes = 1800 seconds
            if len(power_data) >= 1800:
                try:
                    intervals['30m'] = max(PowerCalculator.rolling_average(power_data, time_data, 1800))
                except (ValueError, IndexError):
                    print("⚠️ Insufficient data for 30m power calculation")
                    intervals['30m'] = 0
            else:
                print(f"⚠️ Activity too short for 30m power calculation ({len(power_data)} data points)")
                intervals['30m'] = 0
                
            # 45 minutes = 2700 seconds
            if len(power_data) >= 2700:
                try:
                    intervals['45m'] = max(PowerCalculator.rolling_average(power_data, time_data, 2700))
                except (ValueError, IndexError):
                    print("⚠️ Insufficient data for 45m power calculation")
                    intervals['45m'] = 0
            else:
                print(f"⚠️ Activity too short for 45m power calculation ({len(power_data)} data points)")
                intervals['45m'] = 0
                
            # 1 hour = 3600 seconds
            if len(power_data) >= 3600:
                try:
                    intervals['1hr'] = max(PowerCalculator.rolling_average(power_data, time_data, 3600))
                except (ValueError, IndexError):
                    print("⚠️ Insufficient data for 1hr power calculation")
                    intervals['1hr'] = 0
            else:
                print(f"⚠️ Activity too short for 1hr power calculation ({len(power_data)} data points)")
                intervals['1hr'] = 0
                
            intervals['max'] = max(power_data)
            
            # Calculate normalized power
            np_value = PowerCalculator.calculate_normalized_power(power_data, time_data)
                
            return {
                'best_10m_power': intervals.get('10m', 0),
                'best_20m_power': intervals.get('20m', 0),
                'best_30m_power': intervals.get('30m', 0),
                'best_45m_power': intervals.get('45m', 0),
                'best_1hr_power': intervals.get('1hr', 0),
                'max_power': intervals.get('max', 0),
                'normalized_power': np_value
            }
            
        except Exception as e:
            print(f"❌ Unexpected error in power calculations: {str(e)}")
            return None
    
    @staticmethod
    def rolling_average(power_data, time_data, window_seconds):
        """
        Calculate rolling average power over a specified time window.
        
        Args:
            power_data: List of power values
            time_data: List of timestamps
            window_seconds: Size of rolling window in seconds
            
        Returns:
            list: Rolling average power values
        """
        if not power_data or len(power_data) < 2:
            return [0]
            
        results = []
        
        # For each data point, find the average power over the next window_seconds
        for i in range(len(power_data)):
            # Find the end index for this window
            end_idx = i
            while end_idx < len(time_data) and time_data[end_idx] - time_data[i] < window_seconds:
                end_idx += 1
                
            # If we have a valid window
            if end_idx > i:
                window_data = power_data[i:end_idx]
                if window_data:
                    avg = sum(window_data) / len(window_data)
                    results.append(avg)
        
        return results if results else [0]
    
    @staticmethod
    def calculate_normalized_power(power_data, time_data):
        """
        Calculate normalized power (NP) from power data.
        
        Args:
            power_data: List of power values
            time_data: List of timestamps
            
        Returns:
            float: Normalized power value
        """
        try:
            # Must have at least 30 seconds of data
            if len(power_data) < 30:
                return 0
                
            # Calculate 30-second moving average
            thirty_sec_avg = PowerCalculator.rolling_average(power_data, time_data, 30)
            
            # Calculate the fourth power of each 30s average
            fourth_powers = [pow(avg, 4) for avg in thirty_sec_avg]
            
            # Calculate the average of the fourth powers
            if fourth_powers:
                avg_fourth_power = sum(fourth_powers) / len(fourth_powers)
                
                # Take the fourth root of the average
                np_value = pow(avg_fourth_power, 0.25)
                return np_value
            else:
                return 0
                
        except Exception as e:
            print(f"❌ Error calculating normalized power: {str(e)}")
            return 0