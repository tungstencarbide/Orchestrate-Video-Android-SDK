package com.limelight.videosdk;

import android.content.Context;
import android.media.MediaPlayer;
import android.media.MediaPlayer.OnCompletionListener;
import android.util.AttributeSet;
import android.widget.VideoView;
import com.limelight.videosdk.Constants.PlayerState;

/**
 * This class is a wrapper around the android player default player view.
 * It has the overridden methods for pause, start and seeks,
 * so that these events information can be sent to Player via IMediaControllerCallback object.
 * This information is used for Analytical Reporting.
 * @author kanchan
 */
class VideoPlayerView extends VideoView implements OnCompletionListener{

    private IMediaControllerCallback mListener;
    public PlayerState mPlayerState = PlayerState.stopped;

    VideoPlayerView(final Context context) {
        super(context);
    }

    VideoPlayerView(final Context context, final AttributeSet attrs){
        super(context, attrs);
    }

    VideoPlayerView(final Context context, final AttributeSet attrs, final int defStyle){
        super(context, attrs, defStyle);
    }

    void setMediaControllerCallback(final IMediaControllerCallback listener) {
        mListener = listener;
    }

    @Override
    public void seekTo(int msec) {
        final long before = this.getCurrentPosition();
        super.seekTo(msec);
        final long after = msec;
        if (mListener != null) {
            mListener.onMediaControllerSeek(before, after);
        }
    }

    @Override
    public void pause() {
        mPlayerState = PlayerState.paused;
        if(this.isPlaying()){
            super.pause();
            if (mListener != null) {
                mListener.onMediaControllerPause(this.getCurrentPosition());
            }
        }
    }

    @Override
    public void start() {
        super.start();
        mPlayerState = PlayerState.playing;
        if (mListener != null) {
            mListener.onMediaControllerPlay(this.getCurrentPosition());
        }
    }

    @Override
    public void onCompletion(MediaPlayer mediaPlayer) {
        mPlayerState = PlayerState.completed;
        if (mListener != null) {
            mListener.onMediaControllerComplete();
        }
    }
}
