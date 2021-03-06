package com.limelight.videosdk;

import org.apache.log4j.Logger;
import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.media.MediaPlayer;
import android.media.MediaPlayer.OnCompletionListener;
import android.media.MediaPlayer.OnErrorListener;
import android.media.MediaPlayer.OnPreparedListener;
import android.net.Uri;
import android.os.Bundle;
import android.support.v4.content.LocalBroadcastManager;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.ProgressBar;
import android.widget.RelativeLayout;
import com.limelight.videosdk.Constants.PlayerState;
import com.limelight.videosdk.MediaControl.FullScreenCallback;

/**
 * This class will play the video in full screen.
 *
 */
public class FullScreenPlayer extends Activity implements OnErrorListener,OnPreparedListener, OnCompletionListener,IMediaControllerCallback{
    private static final String TAG = FullScreenPlayer.class.getSimpleName();
    private VideoPlayerView mPlayerView;
    private Logger mLogger;
    private int mPosition;
    private AnalyticsReporter mReporter;
    private String mMediaId;
    private ProgressBar mProgress;
    private boolean isReporting;
    private View.OnClickListener mPlayListNext;
    private View.OnClickListener mPlayListPrev;

    @Override
    protected void onCreate(final Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN);
        final RelativeLayout playerLayout = new RelativeLayout(this);
        playerLayout.setBackgroundColor(Color.BLACK);
        playerLayout.setGravity(Gravity.CENTER);
        mPlayerView = new VideoPlayerView(this);
        final MediaControl mediaController = new MediaControl(this, true);
        mediaController.setFullScreenCallback(new FullScreenCallback() {
            @Override
            public void fullScreen() {
                mLogger.debug(TAG+" Full Screen Should not be Called here");
            }

            @Override
            public void closeFullScreen() {
                close(mPlayerView.getCurrentPosition(), 0);
                mPlayerView.stopPlayback();
            }
        },false);
        mediaController.setAnchorView(mPlayerView);
        mPlayerView.setMediaController(mediaController);
        //This is to stretch the video to full screen
        final RelativeLayout.LayoutParams videoParams = new RelativeLayout.LayoutParams(RelativeLayout.LayoutParams.MATCH_PARENT, RelativeLayout.LayoutParams.MATCH_PARENT);
        videoParams.addRule(RelativeLayout.CENTER_IN_PARENT, RelativeLayout.TRUE);
        playerLayout.addView(mPlayerView,videoParams);
        //old way of adding view
        //playerLayout.addView(mPlayerView);
        final RelativeLayout.LayoutParams params = new RelativeLayout.LayoutParams(RelativeLayout.LayoutParams.WRAP_CONTENT, RelativeLayout.LayoutParams.WRAP_CONTENT);
        params.addRule(RelativeLayout.CENTER_IN_PARENT, RelativeLayout.TRUE);
        mProgress = new ProgressBar(this);
        mProgress.setIndeterminate(true);
        playerLayout.addView(mProgress,params);
        setContentView(playerLayout);
        mPlayerView.setOnErrorListener(this);
        mPlayerView.setOnCompletionListener(this);
        mPlayerView.setMediaControllerCallback(this);
        mLogger = LoggerUtil.getLogger(this);
        mPlayListNext = new View.OnClickListener() {
            @Override
            public void onClick(final View view) {
                close(mPlayerView.getCurrentPosition(), 2);
                mPlayerView.stopPlayback();
            }
        };
        mPlayListPrev = new View.OnClickListener() {
            @Override
            public void onClick(final View view) {
                close(mPlayerView.getCurrentPosition(), 1);
                mPlayerView.stopPlayback();
            }
        };
        final Uri uri = Uri.parse(getIntent().getStringExtra("URI"));
        mPosition  = getIntent().getIntExtra("POSITION",0);
        final String state = getIntent().getStringExtra("STATE");
        mPlayerView.mPlayerState = PlayerState.valueOf(state);
        mMediaId = getIntent().getStringExtra("MEDIAID");
        //Expecting to send true for CHANNELPLAYLIST when media is from channel playlist for all others it can be false.
        if(getIntent().getBooleanExtra("CHANNELPLAYLIST", false)){
            mediaController.setPrevNextListeners(mPlayListNext, mPlayListPrev);
        }
        else{
            //CHANNELPLAYLIST is not true considering the current media is not from channel playlist.
            mediaController.setPrevNextListeners(null, null);
        }
        mPlayerView.setOnPreparedListener(this);
        mPlayerView.setVideoURI(uri);
        mReporter = new AnalyticsReporter(this);
        mLogger.debug(TAG+" Created");
    }

    @Override
    public void onMediaControllerPlay(final long position) {
        if(isReporting && mMediaId!= null){
            mReporter.sendPlayWithPosition(position,mMediaId,null);
        }
    }

    @Override
    public void onMediaControllerPause(final long position) {
        if(isReporting && mMediaId!= null){
            mReporter.sendPauseWithPosition(position,mMediaId,null);
        }
    }

    @Override
    public void onMediaControllerSeek(final long beforePosition, final long afterPosition) {
        if(isReporting && mMediaId!= null){
            mReporter.sendSeekWithPositionBefore(beforePosition, afterPosition,mMediaId,null);
        }
    }

    @Override
    public void onCompletion(final MediaPlayer mediaPlayer) {
        mLogger.debug(TAG+" Completed Playing");
        final int duration = mediaPlayer.getDuration();
        if(mMediaId!= null){
            mReporter.sendMediaComplete(mMediaId, null);
        }
        mPlayerView.mPlayerState = PlayerState.completed;
        mediaPlayer.stop();
        close(duration, 0);
    }

    @Override
    public void onPrepared(final MediaPlayer mediaPlayer) {
        if(mPlayerView.mPlayerState==PlayerState.stopped){
            mediaPlayer.stop();
            close(mPosition, 0);
        }
        else{
            isReporting = false;
            if(mPlayerView.canSeekBackward() || mPlayerView.canSeekForward()){
                mPlayerView.seekTo(mPosition);
            }
            if(mPlayerView.mPlayerState == PlayerState.playing){
                mPlayerView.start();
            }
            isReporting = true;
            mProgress.setVisibility(View.GONE);
        }
    }

    @Override
    public boolean onError(final MediaPlayer mediaPlayer, final int what, final int extra) {
        mPlayerView.mPlayerState = PlayerState.stopped;
        mediaPlayer.stop();
        close(0,0);
        return true;
    }

    /**
     * This is the method to close the FullScreenPlayer and send the current state to normal player.
     * @param position
     */
    private void close(final int position, final int prevNextbuttonsSelected){
        final boolean isSwithcToFullScreen = false;
        //prevNextbuttonsSelected will have the following values
        // 0 - closing full screen normally
        // 1 - previous button selected
        // 2- next button selected
        final Intent intent = new Intent();
        intent.setAction("limelight.intent.action.PLAY_FULLSCREEN");
        intent.putExtra("SWITCHTOFULLSCREEN", isSwithcToFullScreen);
        intent.putExtra("POSITION",position);
        intent.putExtra("STATE",mPlayerView.mPlayerState.name());
        intent.putExtra("PREVNEXTBTNS",prevNextbuttonsSelected);

        LocalBroadcastManager.getInstance(FullScreenPlayer.this).sendBroadcast(intent);
        finish();
    }

    @Override
    public void onDestroy() {
        mReporter.unregisterReceiver();
        super.onDestroy();
    }

    @Override
    public void onBackPressed() {
        if(mPlayerView != null && mPlayerView.mPlayerState != PlayerState.stopped){
            mPosition = mPlayerView.getCurrentPosition();
        }else{
            mPosition = 0;
        }
        close(mPosition, 0);
    }
}
