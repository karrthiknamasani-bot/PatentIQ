const nodemailer = require('nodemailer');

const sendEmail = async (options) => {
  try {
    if (!process.env.SMTP_HOST || !process.env.SMTP_EMAIL || !process.env.SMTP_PASSWORD) {
      throw new Error('SMTP credentials are not fully configured in .env');
    }

    const transporter = nodemailer.createTransport({
      host: process.env.SMTP_HOST,
      port: process.env.SMTP_PORT || 587,
      secure: false, // true for 465, false for other ports
      auth: {
        user: process.env.SMTP_EMAIL,
        pass: process.env.SMTP_PASSWORD,
      },
    });

    const type = options.type || 'otp';
    const otp = options.otp || '000000';
    let subject = options.subject;
    let text = options.text;
    let title = '';
    let description = '';
    
    if (type === 'verify') {
      subject = subject || 'Your PatentIQ Email Verification Code';
      text = text || `Your PatentIQ Email Verification Code is: ${otp}. This OTP expires in 5 minutes.`;
      title = 'Verify Your Email';
      description = 'Please use the following One-Time Password (OTP) to verify your email address and activate your account.';
    } else {
      subject = subject || 'PatentIQ Password Reset OTP';
      text = text || `Your PatentIQ Password Reset OTP is: ${otp}. This OTP expires in 5 minutes.`;
      title = 'Password Reset Request';
      description = 'You requested a password reset for your PatentIQ account. Please use the following One-Time Password (OTP) to proceed.';
    }

    const htmlTemplate = `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 30px; border: 1px solid #e5e7eb; border-radius: 12px; background-color: #ffffff;">
        <div style="text-align: center; margin-bottom: 30px;">
          <h1 style="color: #111827; margin: 0; font-size: 28px; font-weight: 900;">Patent<span style="color: #2563eb;">IQ</span></h1>
        </div>
        <p style="color: #374151; font-size: 16px; line-height: 1.5; font-weight: 600;">${title}</p>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">${description}</p>
        <div style="text-align: center; margin: 40px 0;">
          <div style="background-color: #f3f4f6; color: #111827; padding: 20px 40px; border-radius: 8px; font-weight: 700; display: inline-block; font-size: 32px; letter-spacing: 4px; border: 2px dashed #d1d5db;">
            ${otp}
          </div>
        </div>
        <p style="color: #dc2626; font-size: 14px; text-align: center; font-weight: 500;">This OTP expires in 5 minutes.</p>
        <p style="color: #374151; font-size: 14px; text-align: center; font-weight: 600; margin-top: 10px;">Do not share this OTP with anyone.</p>
        <hr style="border: 0; border-top: 1px solid #f3f4f6; margin: 30px 0;" />
        <p style="color: #9ca3af; font-size: 13px; text-align: center; margin: 0;">If you did not request this OTP, please ignore this email.</p>
      </div>
    `;

    const message = {
      from: process.env.SMTP_FROM || `PatentIQ <${process.env.SMTP_EMAIL}>`,
      to: options.email,
      subject: subject,
      text: text,
      html: htmlTemplate,
    };

    console.log(`[SMTP] Connecting to ${process.env.SMTP_HOST}...`);
    const info = await transporter.sendMail(message);
    console.log(`✓ Email Sent Successfully to ${options.email} [Message ID: ${info.messageId}]`);
    
  } catch (error) {
    console.error('✗ Full sendMail error:');
    console.error(error);
    throw error;
  }
};

module.exports = sendEmail;
