package com.limelight.videosdk;

import java.io.File;
import org.apache.log4j.Level;
import org.apache.log4j.Logger;
import org.apache.log4j.Priority;
import android.content.Context;

/**
 * This class has methods to configure Logging and to Log the messages.
 * It uses Apache Open source logging library Log4J for logging. <p>
 * Log4j is thread-safe and optimized for speed.
 * Log4j supports multiple output appenders per logger.<p>
 * As of now, we will use RollngFileAppender which can log information to a
 * particular file as configured by Limelight Video SDK. In future, if required
 * we can use SMTPAppender or SocketAppender or so.
 * <p>
 * This class will be accessible to customer application so that they can do
 * some little configuration for logging. As of now only few methods like 
 * setLogLevel() will be exposed for customer application.
 * With this method customer application
 * developer can set the level of logging done by SDK.<p>
 * The priority order of levels is: <br><ul>
 * 1. Fatal
 * 2. Error
 * 3. Warn
 * 4. Info
 * 5. Debug</ul>
 * Logs below or equal to current level will only be logged. 
 * eg: If current level is set to error, then only error and fatal logs will be logged.
 * Selecting Off will turn off the logging.<p>
 * LoggerUtil also converts the log levels into some integer values ranging from 0 to 6. 
 * Log4j Levels integer values are difficult to use in code as they are not in sequence.
 * So this method maps Log4J level values to normal continuous integer values.<p>
 * Sample code for using LoggerUtil:<br>
 * LoggerUtil.configure( "LLVSDK.log" , "%d - [%p::%c::%t] - %m%n" , 5 , 1024);<br>
 * LoggerUtil.getLogger( �SDK� ).error( "XXXX" );
 */
public class LoggerUtil {

    private static LogConfigurator sLogConfigurator = new LogConfigurator();
    public final static String LOGGER_NAME = "Limelight_Video_SDK";

    /**
     * Method to configure Logging.
     * @param fileName Name of file where logs will be written
     * @param filePattern set output format of the log line
     * @param maxBackupSize Maximum number of backed up log files
     * @param maxFileSize maximum size of log file until rolling
     */
    static void configure(final String fileName, final String filePattern,
            final int maxBackupSize, final long maxFileSize) {

        sLogConfigurator.setFileName(fileName);
        sLogConfigurator.setFilePattern(filePattern);
        sLogConfigurator.setMaxBackupSize(maxBackupSize);
        sLogConfigurator.setMaxFileSize(maxFileSize);
        sLogConfigurator.configure();
    }

    /**
     * Method to return a logger object.
     * If the log file does not exists then configure the logger and create a log file.
     * @param name Logger name
     * @return {@link Logger}
     */
    public synchronized static Logger getLogger(final Context context,final String name) {
        final String filePath = sLogConfigurator.getFileName();
        if(filePath == null && context != null){
            final File file = new File(context.getFilesDir(), LoggerUtil.LOGGER_NAME + ".log");
            LoggerUtil.configure(file.getAbsolutePath(),"%d - %p - %c - %t - %m%n", 5, 512 * 1024);
        }
        return Logger.getLogger(name);
    }

    /**
     * Developer can set the level of logging done by SDK.<br>
     * The priority order of levels is <br>
     * 1.Fatal 2.Error 3. Warn 4. Info 5. Debug <br>
     * Logs below or equal to current level will only be logged. eg: If current
     * level is set to error, then only error and fatal logs will be logged.<br>
     * Off turns off the logging.
     * 
     * @param level
     */
    public static void setLogLevel(final Level level) {
        if(level != null){
           sLogConfigurator.setLevel(LOGGER_NAME, level);
        }
    }

    /**
     * Method to return the current log level
     * @return {@link Level}
     */
    public static Level getLogLevel() {
        return sLogConfigurator.getLevel(LOGGER_NAME);
    }

    /**
     * Method to return all levels.The levels are in priority order. 1.Debug 2.
     * Info 3. Warn 4. Error 5. Fatal.<br>
     * 
     * @return string[]
     */
    public static String[] getAllLogLevels() {
        return new String[] {
                Level.DEBUG.toString(),
                Level.INFO.toString(),
                Level.WARN.toString(),
                Level.ERROR.toString(),
                Level.FATAL.toString(),
                Level.OFF.toString()
            };
    }

    /**
     * This method converts the log levels into some integer values ranging from 0 to 6.
     * Log4j Levels integer values are difficult to use in code as they are not in sequence
     * So this method maps Log4J level values to normal continuous values.
     * @param level {@link Level}
     * @return int
     */
    public static int levelToInt(final Level level) {
        int retVal = -1;
        if(level != null){
            switch (level.toInt()) {
            case Priority.DEBUG_INT:
                retVal= 0;
                break;
            case Priority.INFO_INT:
                retVal= 1;
                break;
            case Priority.WARN_INT:
                retVal= 2;
                break;
            case Priority.ERROR_INT:
                retVal= 3;
                break;
            case Priority.FATAL_INT:
                retVal= 4;
                break;
            case Priority.OFF_INT:
                retVal= 5;
                break;
            default:
                break;
            }
        }
        return retVal;
    }
}
