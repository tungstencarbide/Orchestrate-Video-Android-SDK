package com.limelight.videosdk;

import java.io.FileDescriptor;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import org.apache.log4j.Logger;
import org.json.JSONException;
import org.json.JSONObject;
import android.app.Activity;
import android.content.Context;
import android.drm.DrmErrorEvent;
import android.drm.DrmEvent;
import android.drm.DrmInfoEvent;
import android.drm.DrmInfoRequest;
import android.drm.DrmManagerClient;
import android.drm.DrmManagerClient.OnErrorListener;
import android.drm.DrmManagerClient.OnEventListener;
import android.drm.DrmManagerClient.OnInfoListener;
import android.drm.DrmStore;
import android.util.Log;
import com.limelight.videosdk.Constants.WidevineStatus;
import com.limelight.videosdk.model.Delivery;
import com.limelight.videosdk.model.Encoding;
import com.limelight.videosdk.model.PrimaryUse;
import com.limelight.videosdk.utility.Downloader;
import com.limelight.videosdk.utility.Downloader.DownLoadCallback;
import com.limelight.videosdk.utility.Setting;

/**
 * This class manages all the widevine related functionality. It checks for the widevine drm engine presence in device and 
 * requests drm engine to fetch license from Limelight server for rights 
 * associated with the media.It then requests DRM engine to validate the rights.
 * It also allows toregister and deregister the DRM engine with organization details.
 * @author kanchan
 */
class WidevineManager implements OnInfoListener,OnEventListener,OnErrorListener{
    private Downloader mWidevineDownloader = null;
    private String mDownloadingUrl = null;
    private Context mContext = null;
    private WVCallback mCallback = null;
    private JSONObject mCredentials = null;
    private DrmManagerClient mDrm = null;
    private String mUri= null;
    private static final String TAG = WidevineManager.class.getSimpleName();
    private Logger mLogger=  null;
    private DrmInfoRequest mDrmInfoRequest = null;
    private FileInputStream mFileStream = null;
    private ContentService mContentService = null;

    public interface WVCallback{
        void onSuccess(String uri);
        void onError(Throwable throwable);
        void onProgress(int percentFinished);
        void onSendMessage(String message);
    }

    WidevineManager(Context ctx,String media,ContentService svc){
        mContext = ctx;
        mLogger = LoggerUtil.getLogger(mContext,LoggerUtil.sLoggerName);
        mContentService = svc;
    }

    /**
     * This method plays wide vine online or wide vine offline encoding.
     * If the encoding primary use is wide vine online it initiates the rights 
     * request and on success it plays the encoding media.
     * If the encoding primary use is wide vine offline , 
     * it downloads the content and then it initiates the rights 
     * request and on success it plays the encoding media.
     * @param encoding Encoding
     * @param cb WVCallback
     */
    void playWidewineEncodedContent(Encoding encoding,WVCallback cb){
        mCallback = cb;
        if(encoding!= null && encoding.primaryUse!= null && encoding.mEncodingUrl!= null && encoding.mMediaID != null){
            mLogger.debug(TAG + " encoding mediaID : " + encoding.mMediaID + " mEncodingUrl :" +encoding.mEncodingUrl);
            if (PrimaryUse.WidevineOffline.equals(encoding.primaryUse)) {
                mLogger.debug(TAG + " Encoding is Widevine download ");
                downloadWidevine(encoding.mEncodingUrl.toString(),encoding.mMediaID,null);
            } else if (encoding.primaryUse.equals(PrimaryUse.Widevine)) {
                try {
                    mLogger.debug(TAG + " Encoding is Widevine online ");
                    requestRights(encoding.mEncodingUrl.toString(), encoding.mMediaID);
                } catch (JSONException e) {
                    mLogger.error(TAG + " "+e != null ?e.getStackTrace():"JSON Exception");
                    if(mCallback!= null)
                        mCallback.onError(new Throwable("AcquireRights Failed !"));
                }
            }
        }else{
            if(mCallback!= null)
                mCallback.onError(new Throwable("Invalid Encodings !"));
        }
    }

    /**
     * This method plays wide vine online or wide vine offline encoding.
     * If the delivery is wide vine online it initiates the rights 
     * request and on success it plays the encoding media.
     * If the delivery is wide vine offline , 
     * it downloads the content and then it initiates the rights 
     * request and on success it plays the encoding media.
     * @param delivery Delivery
     * @param cb WVCallback
     */
    void playWidewineDeliveryContent(Delivery delivery,WVCallback cb){
        mCallback = cb;
        if(delivery!= null && delivery.mRemoteURL != null && delivery.mMediaId != null){
            mLogger.debug(TAG + " delivery mediaId : " + delivery.mMediaId + " mRemoteURL :" +delivery.mRemoteURL);
            if (delivery.mDownloadable && delivery.mProtected) {
                mLogger.debug(TAG + " Delivery is Widevine download ");
                downloadWidevine(delivery.mRemoteURL.toString(),delivery.mMediaId,null);
            } else if (delivery.mProtected) {
                try {
                    mLogger.debug(TAG + " Delivery is Widevine online ");
                    requestRights(delivery.mRemoteURL.toString(),delivery.mMediaId);
                } catch (JSONException e) {
                    mLogger.error(TAG + " " +e != null ?e.getStackTrace():"JSON Exception");
                    if(mCallback!= null)
                        mCallback.onError(new Throwable("AcquireRights Failed !"));
                }
            }
        }else{
            if(mCallback!= null)
                mCallback.onError(new Throwable("Invalid Delivery !"));
        }
    }

    /**
     * Method to download widevine content and then play it after validating the rights.
     * @param url
     * @param mediaId
     * @param saveDirLocation
     */
    private void downloadWidevine(String url, final String mediaId,String saveDirLocation) {
        mLogger.debug(TAG + " widevine download url : " + url + " saveDirLocation :" + saveDirLocation + " mediaId :" + mediaId);
        mDownloadingUrl = url;
        mWidevineDownloader = new Downloader((Activity) mContext);
        mWidevineDownloader.startDownload(url, "video/wvm", saveDirLocation, new DownLoadCallback(){

            @Override
            public void onSuccess(String path) {
                mLogger.debug(TAG + " widevine downloaded file url : " + path);
                try {
                    requestRights(path, mediaId);
                } catch (JSONException e) {
                    mLogger.error(TAG + " "+e != null ?e.getStackTrace():"JSON Exception");
                    if(mCallback!= null)
                        mCallback.onError(new Throwable("AcquireRights Failed !"));
                }
            }

            @Override
            public void onError(Throwable throwable) {
                if(mCallback!= null)
                    mCallback.onError(new Throwable(throwable.getMessage()));
            }

            @Override
            public void onProgress(int percentFinished) {
                if(mCallback!= null)
                    mCallback.onProgress(percentFinished);
            }
        });
    }

    /**
     * It requests drm engine to fetch license from Limelight server for 
     * rights associated with the media.It then requests DRM engine to validate 
     * the rights.
     * @throws JSONException 
     */
    private void requestRights(String uri,String mediaId) throws JSONException {
        if(mCallback!= null)
            mCallback.onSendMessage("Processing Widevine Rights !");
        mLogger.debug(TAG +  "widevine request rights url : " + uri + " mediaId :" + mediaId);
        mUri =  uri;
        WidevineStatus registerStatus = register(uri,mediaId);
        if(!(registerStatus==WidevineStatus.OK))
            return;

        // get our license
        int val = mDrm.acquireRights(mDrmInfoRequest);
        if(val != DrmManagerClient.ERROR_NONE){
            if(mCallback!= null)
                mCallback.onError(new Throwable("AcquireRights Failed"));
        }
        if(mFileStream != null){
            try {
                mFileStream.close();
            } catch (IOException e) {
                mLogger.error(TAG + " IOException In Closing FileInputStream");
            }
        }
    }

    /**
     * This method registers the values like device id user data and media uri to the drm info request.
     * @param userData
     * @param uri
     * @return WidevineStatus
     */
    WidevineStatus registerAsset(String userData,String uri){

        String deviceId = Setting.getDeviceID(mContext);
        mDrmInfoRequest.put("WVCAUserDataKey", userData);
        mDrmInfoRequest.put("WVAssetURIKey", uri.toString());
        mDrmInfoRequest.put("WVDeviceIDKey",deviceId);

        boolean isOffline = uri.toString().startsWith("/");
        if (isOffline) {
            try {
                mFileStream = new FileInputStream(uri.toString());
                FileDescriptor fd = mFileStream.getFD();
                if (fd.valid()) {
                    mLogger.debug(TAG + "FileDescriptorKey : " + fd.toString());
                    mDrmInfoRequest.put("FileDescriptorKey", fd.toString());
                }else{
                    mLogger.debug(TAG + " FileDescriptorKey is invalid");
                    if(mCallback!= null)
                        mCallback.onError(new Throwable("FileDescriptorKey is Invalid !"));
                    if(mFileStream != null){
                        try {
                            mFileStream.close();
                        } catch (IOException e) {
                            mLogger.error(TAG + "IOException In Closing FileInputStream");
                        }
                    }
                    return WidevineStatus.FileSystemError;
                }
            } catch (FileNotFoundException e) {
                if(mCallback!= null)
                    mCallback.onError(new Throwable("File Not Found !"));
                if(mFileStream != null){
                    try {
                        mFileStream.close();
                    } catch (IOException e1) {
                        mLogger.error(TAG + " IOException In Closing FileInputStream");
                    }
                }
                return WidevineStatus.FileNotPresent;
            } catch (IOException e) {
                if(mCallback!= null)
                    mCallback.onError(new Throwable("Error Adding File Key"));
                if(mFileStream != null){
                    try {
                        mFileStream.close();
                    } catch (IOException e1) {
                        mLogger.error(TAG + " IOException In Closing FileInputStream");
                    }
                }
                return WidevineStatus.FileSystemError;
            }
        }
        return WidevineStatus.OK;
    }

    /**
     * This method sets the credentials with media id and organization details 
     * @param mediaID
     * @throws JSONException
     */
    void setMediaCredentials(String mediaID) throws JSONException{
        long clientTime = System.currentTimeMillis() / 1000L;
        String toSign = String.format("%s|%s|%s|get_license|%s",mContentService.getAccessKey(), clientTime, mediaID, mContentService.getOrgId());
        String signature = URLAuthenticator.signWithKey(mContentService.getSecret(), toSign);
        if(signature == null){
            if(mCallback!= null)
                mCallback.onError(new Throwable("Signing Failed !"));
            return;
        }
        // add values to credentials
        if(mCredentials != null){
            mCredentials.put("access_key", mContentService.getAccessKey());
            mCredentials.put("client_time", clientTime);
            mCredentials.put("media_id", mediaID);
            mCredentials.put("operation", "get_license");
            mCredentials.put("organization_id", mContentService.getOrgId());
            mCredentials.put("signature", signature);
        }
    }

    /**
     * This method sets the organization values into drm info request.
     */
    void setOrganizationCredentials(){
        mDrmInfoRequest = new DrmInfoRequest(DrmInfoRequest.TYPE_RIGHTS_ACQUISITION_INFO, "video/wvm");
        mDrmInfoRequest.put("WVDRMServerKey", Setting.getLicenseProxyURL());
        mDrmInfoRequest.put("WVPortalKey", Setting.getPortalKey());
        mDrmInfoRequest.put("WVClientKey", mContentService.getOrgId());
    }

    /**
     * This method first initializes the widevine manager,sets the media credentials 
     * and then registers the assets details by generating userdata from credentials.
     * @param uri
     * @param mediaID
     * @throws JSONException
     */
    private WidevineStatus register(String uri,String mediaID) throws JSONException{
        WidevineStatus initStatus = initialize(mContext);
        if(initStatus != WidevineStatus.OK && initStatus != WidevineStatus.AlreadyInitialized){
            return WidevineStatus.NotRegistered;
        }
        setMediaCredentials(mediaID);
        String userData = null;
        try {
            userData = URLEncoder.encode(mCredentials.toString(), Constants.URL_CHARACTER_ENCODING_TYPE);
        } catch (UnsupportedEncodingException e) {
            mLogger.error(TAG + " " +e != null ?e.getStackTrace():"UnsupportedEncodingException");
            if(mCallback!= null)
                mCallback.onError(new Throwable("Error Encoding JSON"));
            return WidevineStatus.NotRegistered;
        }
        WidevineStatus registerStatus = registerAsset(userData,uri);
        if(registerStatus == WidevineStatus.OK){
            return WidevineStatus.OK;
        }
        return WidevineStatus.NotRegistered;
    }

    private void unRegister(){
        if(mCredentials != null){
            mCredentials.remove("access_key");
            mCredentials.remove("organization_id");
            mCredentials.remove("signature");
            mCredentials.remove("client_time");
            mCredentials.remove("media_id");
            mCredentials.remove("get_license");
        }
        unRegisterAsset();
    }

    private void unRegisterAsset() {
        mDrmInfoRequest.put("WVCAUserDataKey", "");
        mDrmInfoRequest.put("WVAssetURIKey", "");
        mDrmInfoRequest.put("WVDeviceIDKey","");
    }

    /**
     * Method to check whether is device is Widevine DRM enabled.
     * @return true if Widevine Supported else false
     */
    public boolean isWideVineSupported(Context ctx){
        DrmManagerClient drm = new DrmManagerClient(ctx);
        boolean supported = false;
        String[] engines = drm.getAvailableDrmEngines();
        for (String engine : engines) {
            if (engine.contains("Widevine")) {
                supported = true;
                break;
            }
        }
        return supported;
    }

    /**
     * To check availability of widevine DRM engine and on availability, 
     * initialize the drm engine.
     * Also set the organization credentials.
     * @param context
     */
    private WidevineStatus initialize(Context context) {

        if(mDrm == null){
            if (!isWideVineSupported(context)) {
                if(mCallback!= null)
                    mCallback.onError(new Throwable("WideVine Unsupported Device!"));
                return WidevineStatus.NotInitialized;
            }
            mCredentials = new JSONObject();
            mDrm = new DrmManagerClient(mContext);
            mDrm.setOnErrorListener(this);
            mDrm.setOnEventListener(this);
            mDrm.setOnInfoListener(this);
            setOrganizationCredentials();
        }else{
            return WidevineStatus.AlreadyInitialized;
        }
        return WidevineStatus.OK;
    }

    /**
     * This method cancels the widevine offline content download operation.
     */
    void cancelDownload() {
        if(mWidevineDownloader!= null){
            mLogger.debug(TAG + " cancelDownload : " + mDownloadingUrl);
            mWidevineDownloader.cancelDownload(mDownloadingUrl);
        }
    }

    @Override
    public void onError(DrmManagerClient client, DrmErrorEvent event) {
        switch (event.getType()) {
        case DrmErrorEvent.TYPE_PROCESS_DRM_INFO_FAILED:
            if(mCallback!= null)
                mCallback.onError(new Throwable("Failed To Process DRM Info !"));
            break;
        case DrmErrorEvent.TYPE_NO_INTERNET_CONNECTION:
            if(mCallback!= null)
                mCallback.onError(new Throwable("Connection Error !"));
            break;
        case DrmErrorEvent.TYPE_NOT_SUPPORTED:
            if(mCallback!= null)
                mCallback.onError(new Throwable("Response From The Server Cannot Be Handled !"));
            break;
        case DrmErrorEvent.TYPE_OUT_OF_MEMORY:
            if(mCallback!= null)
                mCallback.onError(new Throwable("Memory Allocation Failed During Renewal. !"));
            break;
        case DrmErrorEvent.TYPE_ACQUIRE_DRM_INFO_FAILED:
            if(mCallback!= null)
                mCallback.onError(new Throwable("Failed To Acquire DrmInfo. !"));
            break;
        case DrmErrorEvent.TYPE_REMOVE_ALL_RIGHTS_FAILED:
            if(mCallback!= null)
                mCallback.onError(new Throwable("Failed To Remove The Rights !"));
            break;
        case DrmErrorEvent.TYPE_RIGHTS_NOT_INSTALLED:
            if(mCallback!= null)
                mCallback.onError(new Throwable("Something Went Wrong Installing The Rights. !"));
            break;
        case DrmErrorEvent.TYPE_RIGHTS_RENEWAL_NOT_ALLOWED:
            if(mCallback!= null)
                mCallback.onError(new Throwable("The Server Rejected The Renewal Of Rights. !"));
            break;
        default:
            Log.w(TAG, String.format("Error [%d]: %s", event.getType(), event.getMessage()));
            if(mCallback!= null)
                mCallback.onError(new Throwable("DRM Error: "+event.getMessage()));
            break;
        }
        mLogger.debug(TAG + " onError event: " + event.getType());
    }

    @Override
    public void onEvent(DrmManagerClient client, DrmEvent event) {
        switch (event.getType()) {
        case DrmEvent.TYPE_DRM_INFO_PROCESSED:
            // check if everything went well and play if so
            int status = mDrm.checkRightsStatus(mUri,DrmStore.Action.PLAY);
            switch (status) {
            case DrmStore.RightsStatus.RIGHTS_VALID:
                if(mCallback!= null)
                    mCallback.onSuccess(mUri);
                break;
            case DrmStore.RightsStatus.RIGHTS_NOT_ACQUIRED:
                if(mCallback!= null)
                    mCallback.onError(new Throwable("Rights Not Acquired"));
                break;
            case DrmStore.RightsStatus.RIGHTS_EXPIRED:
                if(mCallback!= null)
                    mCallback.onError(new Throwable("Rights Expired"));
                break;
            case DrmStore.RightsStatus.RIGHTS_INVALID:
                if(mCallback!= null)
                    mCallback.onError(new Throwable("Rights Invalid"));
                break;
            }
            mLogger.debug(TAG + " drm info proicessed status: " + status);
            break;
        case DrmEvent.TYPE_ALL_RIGHTS_REMOVED:
            if(mCallback!= null)
                mCallback.onSendMessage("All rights Removed !");
            break;
        default:
            Log.d(TAG, String.format("Event [%d]: %s", event.getType(),event.getMessage()));
            break;
        }
        mLogger.debug(TAG + " on event: " + event.getType());
    }

    @Override
    public void onInfo(DrmManagerClient client, DrmInfoEvent event) {
        switch (event.getType()) {
        case DrmInfoEvent.TYPE_RIGHTS_INSTALLED:
            Log.i(TAG,"The rights have been successfully downloaded and installed");
            break;
        case DrmInfoEvent.TYPE_ACCOUNT_ALREADY_REGISTERED:
            Log.i(TAG,"The registration has already been done for the given account");
            break;
        case DrmInfoEvent.TYPE_ALREADY_REGISTERED_BY_ANOTHER_ACCOUNT:
            Log.i(TAG,"The registration has already been done by another account ID");
            break;
        case DrmInfoEvent.TYPE_REMOVE_RIGHTS:
            Log.i(TAG, "The rights need to be removed completely");
            break;
        case DrmInfoEvent.TYPE_WAIT_FOR_RIGHTS:
            Log.i(TAG, "The rights object is being delivered to the device.");
            break;
        default:
            Log.i(TAG, "Widevine Demo: INFO: " + event.getMessage());
            break;
        }
        mLogger.debug(TAG + " on info: " + event.getType());
    }

    @Override
    protected void finalize() throws Throwable {
        super.finalize();
        mLogger.debug(TAG + " finalizing");
        cancelDownload();
        unRegister();
        mCredentials = null;
        mDrm = null;
        mWidevineDownloader  = null;
        mFileStream = null;
        mDrmInfoRequest = null;
    }
}
