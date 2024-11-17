class Sound:
    @staticmethod
    def get_filters():
        return {
            'before_options': (
                '-reconnect 1 '
                '-reconnect_streamed 1 '
                '-reconnect_delay_max 5 '
                '-bufsize 1M '
                '-probesize 1M '
                '-analyzeduration 2M '
                '-fflags +nobuffer '
                '-threads 4 '
                '-fastseek '
                '-rw_timeout 15000000 '
            ),
            'options': (
                '-vn '
                '-af "'
                'volume=2.0, '
                'loudnorm=I=-14:TP=-1.5:LRA=11, '
                'equalizer=f=60:width_type=o:width=2:g=5, '
                'equalizer=f=120:width_type=o:width=2:g=4, '
                'equalizer=f=300:width_type=o:width=2:g=3, '
                'equalizer=f=600:width_type=o:width=2:g=2, '
                'equalizer=f=1000:width_type=o:width=2:g=1.5, '
                'equalizer=f=3000:width_type=o:width=2:g=1.5, '
                'equalizer=f=5000:width_type=o:width=2:g=1.2, '
                'equalizer=f=10000:width_type=o:width=2:g=1.8, '
                'equalizer=f=16000:width_type=o:width=2:g=2, '
                'compand=attacks=0.03:decays=0.25:points=-80/-80|-60/-20|-20/-10|0/-3:soft-knee=6, '
                'dynaudnorm=g=10:p=0.9" '
            ),
        }